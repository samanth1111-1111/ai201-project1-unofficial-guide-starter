import gradio as gr
from query import ask


def handle_query(question: str):
    if not question.strip():
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources


with gr.Blocks(title="FIU Off-Campus Housing Guide") as demo:
    gr.Markdown("## FIU Off-Campus Housing Guide\nAsk questions about apartments, rent, reviews, and student experiences near FIU. Answers come only from collected student sources.")

    inp = gr.Textbox(label="Your question", placeholder="e.g. What do students say about maintenance at University Apartments?")
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8, interactive=False)
    sources = gr.Textbox(label="Retrieved from", lines=4, interactive=False)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

if __name__ == "__main__":
    demo.launch()
