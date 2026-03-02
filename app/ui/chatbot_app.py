import gradio as gr
import matplotlib.pyplot as plt
import pandas as pd
import json
from datetime import datetime
from typing import List, Tuple, Dict, Any

from app.agents.compliance_manager import run_compliance_flow, execute_compliance_actions
from app.tools.simulation_tool import simulate_compliance_scenario


class ComplianceChatbot:
    """Conversational chatbot for compliance intelligence with context management"""
    
    def __init__(self):
        self.current_analysis = None
        self.pending_action = None
        self.context = {
            "last_query": None,
            "last_result": None,
            "awaiting_confirmation": False,
            "action_type": None,
            "simulation_params": {}
        }
    
    def reset_context(self):
        """Reset conversation context"""
        self.context = {
            "last_query": None,
            "last_result": None,
            "awaiting_confirmation": False,
            "action_type": None,
            "simulation_params": {}
        }
    
    def format_analysis_response(self, result: Dict[str, Any]) -> str:
        """Format compliance analysis result as conversational response"""
        response = f"""
📊 **Compliance Analysis Complete**

**Executive Summary:**
{result.get('executive_summary', 'N/A')}

**Key Details:**
• Country: {result.get('country', 'N/A')}
• New Rate: {result.get('new_rate', 0)}%
• Effective Date: {result.get('effective_date', 'N/A')}
• Days Until Effective: {result.get('days_until_effective', 0)}

**Financial Impact:**
• Impacted Employees: {result.get('impacted_employees', 0)}
• Annual Cost Increase: ${result.get('annual_cost_increase', 0):,.2f}
• Monthly Cost Increase: ${result.get('monthly_cost_increase', 0):,.2f}

**Risk & Urgency:**
• Risk Level: {result.get('risk_level', 'N/A')}
• Urgency Level: {result.get('urgency_level', 'N/A')}
• Confidence Score: {result.get('confidence', 0)}%

**What would you like to do next?**
• Ask "execute actions" to implement recommended compliance actions
• Ask "run simulation" to test different scenarios
• Ask "show details" for more information
• Ask "show employees" to see impacted employee list
• Or ask any follow-up questions!
"""
        return response
    
    def format_action_items(self, result: Dict[str, Any]) -> str:
        """Format action items as readable text"""
        action_items = result.get('action_items', [])
        if not action_items:
            return "No specific action items identified."
        
        formatted = "**Recommended Actions:**\n"
        for idx, item in enumerate(action_items, 1):
            formatted += f"\n{idx}. {item.get('action', 'N/A')}\n"
            formatted += f"   • Priority: {item.get('priority', 'N/A')}\n"
            formatted += f"   • Timeline: {item.get('timeline', 'N/A')}\n"
            formatted += f"   • Owner: {item.get('owner', 'N/A')}\n"
        return formatted
    
    def process_message(self, message: str, history: List) -> Tuple[str, List, Any, Any]:
        """Process user message and generate response"""
        
        message_lower = message.lower().strip()
        
        # Handle "new analysis" or "reset" commands
        if any(word in message_lower for word in ["new analysis", "reset", "start over", "clear"]):
            self.reset_context()
            self.current_analysis = None
            response = "Context cleared! Ready for a new compliance analysis. What would you like to analyze?"
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response})
            return response, history, None, None
        
        # Handle action confirmation
        if self.context.get("awaiting_confirmation"):
            if any(word in message_lower for word in ["yes", "confirm", "proceed", "execute", "do it"]):
                return self._execute_pending_action(history)
            elif any(word in message_lower for word in ["no", "cancel", "stop", "abort"]):
                self.context["awaiting_confirmation"] = False
                self.context["action_type"] = None
                response = "Action cancelled. What else can I help you with?"
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})
                return response, history, None, None
        
        # Handle follow-up queries about existing analysis
        if self.current_analysis:
            # Show detailed recommendations
            if any(word in message_lower for word in ["detail", "recommendation", "more info"]):
                response = f"""
**Detailed Recommendations:**

{self.current_analysis.get('recommendations', 'No detailed recommendations available.')}

{self.format_action_items(self.current_analysis)}

Would you like me to execute these actions?
"""
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})
                return response, history, None, None
            
            # Show employee details
            elif any(word in message_lower for word in ["employee", "staff", "worker", "people"]):
                employee_rows = self.current_analysis.get('employee_rows', [])
                if employee_rows:
                    df = pd.DataFrame(employee_rows)
                    response = f"""
**Impacted Employees ({len(employee_rows)} total):**

I've prepared a detailed table showing all impacted employees. You can download the CSV report for complete details.

Key Statistics:
• Total Impacted: {self.current_analysis.get('impacted_employees', 0)}
• Annual Cost Impact: ${self.current_analysis.get('annual_cost_increase', 0):,.2f}

Would you like to see the visualization or execute actions?
"""
                    history.append({"role": "user", "content": message})
                    history.append({"role": "assistant", "content": response})
                    return response, history, df, None
                else:
                    response = "No employee data available for this analysis."
                    history.append({"role": "user", "content": message})
                    history.append({"role": "assistant", "content": response})
                    return response, history, None, None
            
            # Execute actions
            elif any(word in message_lower for word in ["execute", "implement", "perform action", "do it", "proceed"]):
                self.context["awaiting_confirmation"] = True
                self.context["action_type"] = "execute"
                response = f"""
**Ready to Execute Compliance Actions**

This will automatically:
✓ Update payroll configurations
✓ Notify payroll teams
✓ Create compliance tickets
✓ Log audit entries
✓ Generate executive reports
✓ Schedule compliance reviews

**Confirm execution?** (Reply "yes" to proceed or "no" to cancel)
"""
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})
                return response, history, None, None
            
            # Run simulation - improved parameter extraction
            elif any(word in message_lower for word in ["simulat", "what if", "scenario"]) or ("test" in message_lower and ("rate" in message_lower or "delay" in message_lower or "default" in message_lower)):
                # Try to extract parameters from message
                import re
                
                rate_match = re.search(r'(\d+(?:\.\d+)?)\s*%?\s*rate', message_lower)
                delay_match = re.search(r'(\d+)\s*days?\s*delay', message_lower)
                impl_match = re.search(r'(\d+)\s*%?\s*implementation', message_lower)
                
                print(f"\n[CHATBOT] Simulation request detected")
                print(f"  Message: {message}")
                print(f"  Rate match: {rate_match.group(1) if rate_match else None}")
                print(f"  Delay match: {delay_match.group(1) if delay_match else None}")
                print(f"  Impl match: {impl_match.group(1) if impl_match else None}")
                
                if rate_match or delay_match or impl_match or "default" in message_lower:
                    # Extract values or use None for defaults
                    rate = float(rate_match.group(1)) if rate_match else None
                    delay = int(delay_match.group(1)) if delay_match else None
                    impl = float(impl_match.group(1)) if impl_match else None
                    
                    print(f"  Running simulation with: rate={rate}, delay={delay}, impl={impl}")
                    return self._run_simulation(history, rate, delay, impl)
                else:
                    # Ask for parameters
                    response = """
**Simulation Mode**

I can run what-if scenarios to test different outcomes. Please provide:

1. **Scenario Rate** (e.g., "test with 25% rate")
2. **Implementation Delay** (e.g., "delay by 30 days")
3. **Implementation Percentage** (e.g., "90% implementation")

Or simply say "run default simulation" to use current values.

**Examples:**
• "run default simulation"
• "simulate with 28% rate"
• "test with 25% rate and 45 days delay"
• "run simulation with 30% rate, 60 days delay, and 85% implementation"
"""
                    history.append({"role": "user", "content": message})
                    history.append({"role": "assistant", "content": response})
                    return response, history, None, None
            
            # Run default simulation (kept for backward compatibility)
            elif "default simulation" in message_lower:
                return self._run_simulation(history, None, None, None)
            
            # Show visualization
            elif any(word in message_lower for word in ["chart", "graph", "visual", "plot"]):
                fig = self._create_visualization(self.current_analysis)
                response = "Here's the visual analysis of the compliance impact."
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})
                return response, history, None, fig
        
        # New compliance query - check for compliance-related keywords OR if no current analysis
        # This ensures any query about rates, countries, dates, etc. triggers analysis
        compliance_keywords = [
            "compliance", "regulation", "law", "rate", "contribution", "pension", "social",
            "germany", "france", "uk", "united kingdom", "effective", "increase", "decrease",
            "change", "april", "march", "june", "january", "%", "percent", "2026", "2025", "2024"
        ]
        
        is_compliance_query = (
            any(word in message_lower for word in compliance_keywords) or
            not self.current_analysis  # If no analysis yet, treat as new query
        )
        
        if is_compliance_query and not self.current_analysis:
            return self._analyze_compliance(message, history)
        
        # Help and general queries
        elif any(word in message_lower for word in ["help", "what can you do", "capabilities"]):
            response = """
**I'm your Compliance Intelligence Assistant!** 🤖

I can help you with:

📊 **Compliance Analysis**
• Analyze regulatory changes and their impact
• Calculate financial implications
• Assess risk and urgency levels
• Identify impacted employees

⚡ **Action Execution**
• Update payroll configurations
• Notify relevant teams
• Create compliance tickets
• Generate reports

🔬 **Scenario Simulation**
• Test different implementation scenarios
• Compare financial outcomes
• Assess risk variations

Just describe a compliance change (e.g., "Germany increased pension contribution to 22% effective next month") and I'll handle the rest!

What would you like to do?
"""
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response})
            return response, history, None, None
        
        # Default response for unclear queries
        else:
            response = """
I'm not sure I understand. I can help you with:

• Analyzing compliance and regulatory changes
• Executing compliance actions
• Running what-if simulations
• Showing detailed reports and employee impacts

Try asking something like:
• "Analyze Germany pension rate increase to 22%"
• "Show me the impacted employees"
• "Execute the recommended actions"
• "Run a simulation"

What would you like to know?
"""
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response})
            return response, history, None, None
    
    def _analyze_compliance(self, query: str, history: List) -> Tuple[str, List, Any, Any]:
        """Perform compliance analysis"""
        try:
            print(f"\n{'='*60}")
            print(f"🔍 CHATBOT: Starting compliance analysis")
            print(f"Query: {query}")
            print(f"{'='*60}\n")
            
            # Add user message
            history.append({"role": "user", "content": query})
            
            # Show processing message
            processing_msg = "🔄 Analyzing compliance impact... This may take a moment."
            history.append({"role": "assistant", "content": processing_msg})
            
            # Run analysis
            print("Calling run_compliance_flow...")
            result = run_compliance_flow(query)
            print(f"Analysis complete. Result keys: {result.keys()}")
            print(f"Impacted employees: {result.get('impacted_employees', 0)}")
            print(f"Country: {result.get('country', 'N/A')}")
            
            self.current_analysis = result
            self.context["last_query"] = query
            self.context["last_result"] = result
            
            # Format response
            response = self.format_analysis_response(result)
            
            # Create visualization
            fig = self._create_visualization(result)
            
            # Update history with final response
            history[-1] = {"role": "assistant", "content": response}
            
            print(f"\n{'='*60}")
            print(f"✓ CHATBOT: Analysis complete")
            print(f"{'='*60}\n")
            
            return response, history, None, fig
            
        except Exception as e:
            import traceback
            print(f"\n{'='*60}")
            print(f"❌ CHATBOT ERROR:")
            print(f"{'='*60}")
            print(traceback.format_exc())
            print(f"{'='*60}\n")
            
            error_response = f"❌ Error analyzing compliance: {str(e)}\n\nPlease try rephrasing your query or ask for help."
            if len(history) > 0 and history[-1].get("role") == "assistant":
                history[-1] = {"role": "assistant", "content": error_response}
            else:
                history.append({"role": "assistant", "content": error_response})
            return error_response, history, None, None
    
    def _execute_pending_action(self, history: List) -> Tuple[str, List, Any, Any]:
        """Execute the pending action"""
        try:
            if not self.current_analysis:
                response = "No analysis available to execute actions on. Please run an analysis first."
                history.append({"role": "user", "content": "Confirm"})
                history.append({"role": "assistant", "content": response})
                return response, history, None, None
            
            # Execute actions
            execution_result = execute_compliance_actions(self.current_analysis, auto_execute=True)
            
            if execution_result.get("status") == "success":
                response = f"""
✅ **Actions Executed Successfully!**

**Actions Performed:**
{chr(10).join(['• ' + action for action in execution_result.get('actions_performed', [])])}

**Execution Details:**
{execution_result.get('execution_output', '')}

All compliance actions have been completed. Is there anything else you'd like to do?
"""
            else:
                response = f"❌ Execution Failed: {execution_result.get('error', 'Unknown error')}"
            
            self.context["awaiting_confirmation"] = False
            self.context["action_type"] = None
            history.append({"role": "user", "content": "Yes, proceed"})
            history.append({"role": "assistant", "content": response})
            return response, history, None, None
            
        except Exception as e:
            error_response = f"❌ Error executing actions: {str(e)}"
            history.append({"role": "user", "content": "Yes, proceed"})
            history.append({"role": "assistant", "content": error_response})
            return error_response, history, None, None
    
    def _run_simulation(self, history: List, rate: float = None, delay: int = None, pct: float = None) -> Tuple[str, List, Any, Any]:
        """Run compliance simulation"""
        try:
            if not self.current_analysis:
                response = "No analysis available to simulate. Please run an analysis first."
                history.append({"role": "user", "content": "Run simulation"})
                history.append({"role": "assistant", "content": response})
                return response, history, None, None
            
            country = self.current_analysis.get("country", "")
            base_rate = self.current_analysis.get("new_rate", 0) / 100
            
            # Use defaults if not provided
            scenario_rate = (rate or self.current_analysis.get("new_rate", 20)) / 100
            delay_days = delay or 0
            implementation_pct = (pct or 100) / 100
            
            simulation = simulate_compliance_scenario(
                country=country,
                base_rate=base_rate,
                scenario_rate=scenario_rate,
                implementation_delay_days=int(delay_days),
                partial_implementation_pct=implementation_pct
            )
            
            # Create comparison chart
            fig = self._create_simulation_chart(simulation)
            
            response = f"""
🔍 **Simulation Results**

**Scenario:** {simulation['scenario_name']}

**Financial Impact:**
• Base Annual Cost: ${simulation['base_annual_cost']:,.2f}
• Scenario Annual Cost: ${simulation['scenario_annual_cost']:,.2f}
• Cost Delta: ${simulation['annual_cost_delta']:,.2f}

**Workforce Impact:**
• Impacted: {simulation['impacted_employees']} / {simulation['total_employees']} employees

**Risk Assessment:**
• Risk Score: {simulation['adjusted_risk_score']}
• {simulation['risk_notes']}

**Parameters:**
• Delay: {simulation['implementation_delay_days']} days
• Implementation: {simulation['partial_implementation_pct']*100}%

Would you like to try a different scenario?
"""
            
            history.append({"role": "user", "content": "Run simulation"})
            history.append({"role": "assistant", "content": response})
            return response, history, None, fig
            
        except Exception as e:
            error_response = f"❌ Simulation Error: {str(e)}"
            history.append({"role": "user", "content": "Run simulation"})
            history.append({"role": "assistant", "content": error_response})
            return error_response, history, None, None
    
    def _create_visualization(self, result: Dict[str, Any]) -> Any:
        """Create impact visualization"""
        try:
            if result.get("impacted_employees", 0) > 0:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
                
                # Impact bar chart
                ax1.bar(["Impacted Employees"], [result["impacted_employees"]], color='#3498db')
                ax1.set_title("Workforce Impact")
                ax1.set_ylabel("Number of Employees")
                
                # Financial exposure
                annual_cost = result.get("annual_cost_increase", 0)
                monthly_cost = result.get("monthly_cost_increase", 0)
                ax2.bar(["Monthly", "Annual"], [monthly_cost, annual_cost], color=['#e74c3c', '#c0392b'])
                ax2.set_title("Financial Exposure")
                ax2.set_ylabel("Cost Increase ($)")
                
                plt.tight_layout()
                return fig
        except Exception:
            pass
        return None
    
    def _create_simulation_chart(self, simulation: Dict[str, Any]) -> Any:
        """Create simulation comparison chart"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Cost comparison
            ax1.bar(
                ["Base Scenario", "Simulated Scenario"],
                [simulation["base_annual_cost"], simulation["scenario_annual_cost"]],
                color=['#3498db', '#e74c3c']
            )
            ax1.set_title("Annual Cost Comparison")
            ax1.set_ylabel("Annual Cost ($)")
            
            # Risk comparison
            ax2.bar(
                ["Base Risk", "Adjusted Risk"],
                [50, simulation["adjusted_risk_score"]],
                color=['#2ecc71', '#e67e22']
            )
            ax2.set_title("Risk Score Comparison")
            ax2.set_ylabel("Risk Score")
            
            plt.tight_layout()
            return fig
        except Exception:
            return None


def launch_chatbot_app():
    """Launch the conversational chatbot interface"""
    
    chatbot = ComplianceChatbot()
    
    with gr.Blocks(title="Compliance Intelligence Chatbot", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🤖 Compliance Intelligence Chatbot
        ### Your AI-powered assistant for regulatory compliance analysis and action execution
        
        Ask me anything about compliance changes, and I'll analyze the impact, recommend actions, and execute them for you!
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                chatbot_interface = gr.Chatbot(
                    label="Compliance Assistant",
                    height=500,
                    show_label=True,
                    avatar_images=(None, "🤖")
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="Your Message",
                        placeholder="Ask about compliance changes, request actions, or ask follow-up questions...",
                        lines=2,
                        scale=4
                    )
                    submit_btn = gr.Button("Send", variant="primary", scale=1)
                
                with gr.Row():
                    clear_btn = gr.Button("Clear Chat", size="sm")
                    examples_btn = gr.Button("Show Examples", size="sm")
            
            with gr.Column(scale=1):
                gr.Markdown("### 📊 Visual Insights")
                chart_output = gr.Plot(label="Impact Visualization")
                
                gr.Markdown("### 👥 Employee Data")
                employee_table = gr.Dataframe(
                    label="Impacted Employees",
                    visible=True,
                    interactive=False
                )
        
        # Example queries
        with gr.Accordion("💡 Example Queries", open=False):
            gr.Examples(
                examples=[
                    "Germany increased social security contribution to 22% effective next month",
                    "Analyze France pension rate change to 18.5% starting January 2026",
                    "Show me the impacted employees",
                    "Execute the recommended actions",
                    "Run a simulation with 25% rate",
                    "What are the detailed recommendations?",
                    "Help me understand the risk assessment"
                ],
                inputs=msg
            )
        
        # Event handlers
        def respond(message, chat_history):
            response, updated_history, emp_data, chart = chatbot.process_message(message, chat_history)
            return "", updated_history, emp_data, chart
        
        def clear_chat():
            chatbot.reset_context()
            chatbot.current_analysis = None
            return [], None, None
        
        def show_examples():
            return """
**Try these example queries:**

📊 Compliance Analysis:
• "Germany increased pension contribution to 22% next month"
• "Analyze UK social security rate change to 15%"

⚡ Actions:
• "Execute the recommended actions"
• "Show me the action items"

🔬 Simulations:
• "Run a simulation"
• "Test with 25% rate and 30 days delay"

📈 Details:
• "Show impacted employees"
• "What are the detailed recommendations?"
• "Show me the visualization"
"""
        
        submit_btn.click(
            respond,
            inputs=[msg, chatbot_interface],
            outputs=[msg, chatbot_interface, employee_table, chart_output]
        )
        
        msg.submit(
            respond,
            inputs=[msg, chatbot_interface],
            outputs=[msg, chatbot_interface, employee_table, chart_output]
        )
        
        clear_btn.click(
            clear_chat,
            outputs=[chatbot_interface, employee_table, chart_output]
        )
        
        examples_btn.click(
            show_examples,
            outputs=msg
        )
    
    demo.launch(share=False)


if __name__ == "__main__":
    launch_chatbot_app()
