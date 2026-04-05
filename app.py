"""
Gradio UI for OpenEnv AI Security Environment
Interactive cybersecurity threat detection evaluation
"""

import gradio as gr
import json
import os
from typing import Dict, Any, List

from environment import AiSecurityEnv
from inference import run_benchmark


class OpenEnvUI:
    """OpenEnv UI handler"""
    
    def __init__(self):
        self.env = AiSecurityEnv(seed=42)
    
    def get_tasks(self) -> List[str]:
        """Get available tasks"""
        return [
            "Data Leakage Prevention (Easy)",
            "Threat Detection (Medium)",
            "Advanced Threat Response (Hard)"
        ]
    
    def run_task(self, task_name: str) -> Dict[str, Any]:
        """Run selected task"""
        try:
            task_map = {
                "Data Leakage Prevention (Easy)": 0,
                "Threat Detection (Medium)": 1,
                "Advanced Threat Response (Hard)": 2
            }
            
            result = run_benchmark(num_episodes=1)
            return result
        except Exception as e:
            return {"error": str(e)}


def create_ui() -> gr.Blocks:
    """Create Gradio interface"""
    ui = OpenEnvUI()
    
    with gr.Blocks(title="AI Security OpenEnv", theme=gr.themes.Soft()) as demo:
        
        gr.Markdown("""
        # Security OpenEnv
        
        Evaluate AI cybersecurity threat detection and response
        """)
        
        with gr.Row():
            task_dropdown = gr.Dropdown(
                choices=ui.get_tasks(),
                label="Select Task",
                value=ui.get_tasks()[0]
            )
            run_btn = gr.Button("Run", variant="primary")
        
        results = gr.JSON(label="Results")
        
        def execute(task_name):
            return ui.run_task(task_name)
        
        run_btn.click(fn=execute, inputs=[task_dropdown], outputs=[results])
    
    return demo


def main():
    """Launch UI"""
    port = int(os.environ.get("PORT", 7860))
    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=port, show_error=True)


if __name__ == "__main__":
    main()