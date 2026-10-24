import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MAX_CHAT_MESSAGES } from "../api";
import { mockApi } from "../testing";
import { ScanChat } from "./ScanChat";

afterEach(() => vi.unstubAllGlobals());

const CHAT = "POST /api/scans/7/chat";
const ANSWER = "formatInvoice has no other use in the repo, so it's safe to stop exporting.";

function renderChat(handler: Parameters<typeof mockApi>[0][string] = () => ({ body: { reply: ANSWER } })) {
  const api = mockApi({ [CHAT]: handler });
  render(<ScanChat scanId={7} />);
  return api;
}

const openPanel = () => userEvent.click(screen.getByRole("button", { name: "Ask about these results" }));
const question = () => screen.getByLabelText("Your question");
const send = () => screen.getByRole("button", { name: /^(Send question|Asking)$/ });

async function ask(text: string) {
  await userEvent.type(question(), text);
  await userEvent.click(send());
}

describe("the chat panel", () => {
  it("starts closed, with a heading and a button that says it's closed", () => {
    renderChat();
    expect(screen.getByRole("heading", { level: 2, name: "Questions about this scan" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ask about these results" })).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByLabelText("Your question")).toBeNull();
  });

  it("opens to a question field that is ready to type in, with starters, and says what it is", async () => {
    renderChat();
    await openPanel();
    expect(screen.getByRole("button", { name: "Hide questions" })).toHaveAttribute("aria-expanded", "true");
    expect(question()).toHaveFocus();
    expect(screen.getByText(/Answers come from this scan, and nothing in your code is changed/)).toBeInTheDocument();
    expect(screen.getByText(/An AI model writes these answers from this scan's findings/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Explain why these items were flagged" })).toBeInTheDocument();
    // Nothing to send yet, and it is never the page's one main action.
    expect(send()).toBeDisabled();
    expect(document.querySelectorAll(".btn-primary")).toHaveLength(0);
  });

  it("sends the question and shows it and the answer, each with who said it", async () => {
    const { calls } = renderChat();
    await openPanel();
    await ask("Is formatInvoice safe to remove?");

    const conversation = await screen.findByRole("list", { name: "Conversation" });
    const [you, lopper] = within(conversation).getAllByRole("listitem");
    expect(within(you).getByText("You")).toBeInTheDocument();
    expect(within(you).getByText("Is formatInvoice safe to remove?")).toBeInTheDocument();
    expect(within(lopper).getByText("Lopper")).toBeInTheDocument();
    expect(within(lopper).getByText(ANSWER)).toBeInTheDocument();
    expect(calls).toEqual([{ key: CHAT, body: { messages: [{ role: "user", content: "Is formatInvoice safe to remove?" }] } }]);
    // The field is empty again and the starters have done their job.
    expect(question()).toHaveValue("");
    expect(screen.queryByRole("button", { name: "Explain why these items were flagged" })).toBeNull();
  });

  it("sends the whole conversation each time, because the server keeps none", async () => {
    let n = 0;
    const { calls } = renderChat(() => ({ body: { reply: `Answer ${++n}` } }));
    await openPanel();
    await ask("First");
    await screen.findByText("Answer 1");
    await ask("Second");
    await screen.findByText("Answer 2");
    expect(calls[1].body).toEqual({
      messages: [
        { role: "user", content: "First" },
        { role: "assistant", content: "Answer 1" },
        { role: "user", content: "Second" },
      ],
    });
  });

  it("sends on Enter and starts a new line on Shift and Enter", async () => {
    const { calls } = renderChat();
    await openPanel();
    await userEvent.type(question(), "one{Shift>}{Enter}{/Shift}two");
    expect(calls).toHaveLength(0);
    expect(question()).toHaveValue("one\ntwo");
    await userEvent.type(question(), "{Enter}");
    await screen.findByText(ANSWER);
    expect(calls).toHaveLength(1);
    expect((calls[0].body as { messages: { content: string }[] }).messages[0].content).toBe("one\ntwo");
  });

  it("sends a starter question as it is written", async () => {
    const { calls } = renderChat();
    await openPanel();
    await userEvent.click(screen.getByRole("button", { name: "Tell me what to check before I merge" }));
    await screen.findByText(ANSWER);
    expect(calls[0].body).toEqual({ messages: [{ role: "user", content: "Tell me what to check before I merge" }] });
  });

  it("won't send an empty question", async () => {
    const { calls } = renderChat();
    await openPanel();
    await userEvent.type(question(), "   {Enter}");
    expect(calls).toHaveLength(0);
    expect(send()).toBeDisabled();
  });

  it("limits a question to what the server accepts", async () => {
    renderChat();
    await openPanel();
    expect(question()).toHaveAttribute("maxlength", "1000");
  });

  it("says what it is doing while it waits, and keeps the field for the next question", async () => {
    let answer!: (reply: string) => void;
    const waiting = new Promise<string>((resolve) => (answer = resolve));
    renderChat(async () => ({ body: { reply: await waiting } }));
    await openPanel();
    await ask("Why?");

    expect(await screen.findByRole("status")).toHaveTextContent("Reading the scan");
    expect(send()).toBeDisabled();
    expect(send()).toHaveAttribute("aria-busy", "true");
    expect(send()).toHaveTextContent("Asking");
    expect(screen.getByRole("button", { name: "Start over" })).toBeDisabled();
    // The question is already on the page, and a second one can't be sent until this one is answered.
    expect(screen.getByText("Why?")).toBeInTheDocument();
    await userEvent.type(question(), "Another{Enter}");
    expect(screen.getAllByRole("listitem")).toHaveLength(1);

    answer("Because nothing imports it.");
    expect(await screen.findByText("Because nothing imports it.")).toBeInTheDocument();
    expect(screen.queryByRole("status")).toBeNull();
    expect(send()).toHaveTextContent("Send question");
    expect(question()).toHaveValue("Another");
  });

  it("shows the server's reason, hands the question back and lets you send it again", async () => {
    let fail = true;
    const { calls } = renderChat(() =>
      fail
        ? { status: 502, body: { error: "We couldn't get an answer just now. Try again in a moment. Nothing has been changed.", code: "chat_failed" } }
        : { body: { reply: ANSWER } },
    );
    await openPanel();
    await ask("Why was this flagged?");

    expect(await screen.findByRole("alert")).toHaveTextContent("We couldn't get an answer just now. Try again in a moment.");
    expect(question()).toHaveValue("Why was this flagged?");
    expect(screen.queryByRole("list", { name: "Conversation" })).toBeNull();

    fail = false;
    await userEvent.click(send());
    expect(await screen.findByText(ANSWER)).toBeInTheDocument();
    expect(screen.queryByRole("alert")).toBeNull();
    // The retry is one question, not two in a row: the server would refuse that.
    expect(calls[1].body).toEqual({ messages: [{ role: "user", content: "Why was this flagged?" }] });
  });

  it("explains a rate limit in the server's words", async () => {
    renderChat(() => ({
      status: 429,
      body: { error: "That's a lot of questions in a minute. Wait a moment and try again. Nothing has been changed.", code: "rate_limited" },
    }));
    await openPanel();
    await ask("Why?");
    expect(await screen.findByRole("alert")).toHaveTextContent("Wait a moment and try again");
  });

  it("explains when the server can't be reached", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    render(<ScanChat scanId={7} />);
    await openPanel();
    await ask("Why?");
    expect(await screen.findByRole("alert")).toHaveTextContent("We couldn't reach the Lopper server");
    expect(question()).toHaveValue("Why?");
  });

  it("shows an answer as plain text, so nothing in it can run or change the page", async () => {
    renderChat(() => ({ body: { reply: '<img src=x onerror="alert(1)"> **not bold** <b>x</b>' } }));
    await openPanel();
    await ask("Hi");
    expect(await screen.findByText(/not bold/)).toHaveTextContent('<img src=x onerror="alert(1)"> **not bold** <b>x</b>');
    expect(document.querySelector("img, b")).toBeNull();
  });

  it("keeps line breaks in an answer", async () => {
    renderChat(() => ({ body: { reply: "- formatInvoice\n- parseLegacyToken" } }));
    await openPanel();
    await ask("Which?");
    expect(await screen.findByText(/formatInvoice/)).toHaveClass("whitespace-pre-wrap");
  });

  it("starts over with an empty conversation, an empty field and the starters back", async () => {
    renderChat();
    await openPanel();
    await ask("Why?");
    await screen.findByText(ANSWER);
    await userEvent.type(question(), "half a thought");
    await userEvent.click(screen.getByRole("button", { name: "Start over" }));
    expect(screen.queryByRole("list", { name: "Conversation" })).toBeNull();
    expect(question()).toHaveValue("");
    expect(screen.getByRole("button", { name: "Explain why these items were flagged" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Start over" })).toBeNull();
  });

  it("keeps the conversation when it is hidden and shown again", async () => {
    renderChat();
    await openPanel();
    await ask("Why?");
    await screen.findByText(ANSWER);
    await userEvent.click(screen.getByRole("button", { name: "Hide questions" }));
    expect(screen.queryByText(ANSWER)).toBeNull();
    await openPanel();
    expect(screen.getByText(ANSWER)).toBeInTheDocument();
  });

  it("stops at the longest conversation the server takes, and says how to go on", async () => {
    const { calls } = renderChat();
    await openPanel();
    const exchanges = MAX_CHAT_MESSAGES / 2;
    for (let i = 1; i <= exchanges; i++) {
      fireEvent.change(question(), { target: { value: `Question ${i}` } });
      await userEvent.click(send());
      await waitFor(() => expect(screen.getAllByRole("listitem")).toHaveLength(i * 2));
      if (i < exchanges) expect(send()).toBeDisabled(); // the field was emptied
    }
    expect((calls.at(-1)!.body as { messages: unknown[] }).messages).toHaveLength(MAX_CHAT_MESSAGES - 1);
    expect(screen.getByText(/as long as it can get/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Your question")).toBeNull();
    expect(send()).toBeDisabled();

    await userEvent.click(screen.getByRole("button", { name: "Start over" }));
    expect(question()).toBeInTheDocument();
  });
});
