import gradio as gr

def greet(name):
    return f"Hello, {name}!"

# Create a Gradio interface
interface = gr.Interface(fn=greet, inputs="text", outputs="text")

if __name__ == "__main__":
    # Launch the interface
    interface.launch()
