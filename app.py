import gradio as gr

def greet(name):
    return f"Hello, {name}!"

interface = gr.Interface(fn=greet, inputs="text", outputs="text")

if __name__ == "__main__":
    interface.launch(server_name="0.0.0.0", server_port=7860)

