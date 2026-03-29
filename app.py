import streamlit as st
import requests
import json
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from dotenv import load_dotenv
import os

# ---------------- CONFIG ----------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ✅ FIXED MODEL (working one)
MODEL = "llama-3.1-8b-instant"

# ---------------- UI CONFIG ----------------
st.set_page_config(page_title="Real-Time Debate Coach", layout="wide")
st.markdown("""
<style>

/* 🔷 Expander (View Analysis bar) */
.streamlit-expanderHeader {
    background: linear-gradient(90deg, #6366f1, #38bdf8);
    color: white !important;
    font-weight: bold;
    border-radius: 10px;
    padding: 10px;
}

/* 🔷 Expander content */
.streamlit-expanderContent {
    background-color: #f1f5f9;
    border-radius: 10px;
    padding: 10px;
}

/* 🔷 Headings */
.highlight-title {
    color: #2563eb;
    font-size: 18px;
    font-weight: bold;
    margin-top: 10px;
}

/* 🔷 Feedback box */
.feedback-box {
    background-color: #e0f2fe;
    padding: 10px;
    border-radius: 10px;
    border-left: 5px solid #38bdf8;
}

/* 🔷 Argument box */
.argument-box {
    background-color: #fef3c7;
    padding: 10px;
    border-radius: 10px;
    border-left: 5px solid #f59e0b;
}

</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* All buttons */
.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, #38bdf8, #6366f1);
    color: white;
    border-radius: 12px;
    padding: 0.6em 1.2em;
    font-weight: 600;
    border: none;
    transition: 0.3s;
}

/* Hover effect */
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

st.title("🧠 Real-Time Debate Coach")
st.markdown("Improve your debate skills with AI-powered feedback")

# ---------------- SESSION STATE ----------------
if "history" not in st.session_state:
    st.session_state.history = []

# ---------------- FUNCTION: CALL GROQ ----------------
def get_ai_feedback(argument):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""You are an expert debate analyst.

Analyze the following debate argument:

"{argument}"

Return STRICTLY in this format:

Score: X/10

Strength:
- Write 2-3 strong points

Logical Fallacies:
- Mention if any (or None)

Suggestions:
- Give 2-3 improvements
"""

    data = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"API Error: {str(e)}"

# ---------------- FUNCTION: GENERATE PDF ----------------
import matplotlib.pyplot as plt
from reportlab.platypus import Image

def generate_pdf(data):
    import matplotlib.pyplot as plt
    from reportlab.platypus import Image
    import re

    file_path = "debate_report.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()

    # 🔥 Increase font sizes
    styles['Title'].fontSize = 20
    styles['Heading2'].fontSize = 16
    styles['Normal'].fontSize = 12

    content = []

    # ---------------- TITLE ----------------
    content.append(Paragraph("<b>AI Debate Analysis Report</b>", styles['Title']))
    content.append(Spacer(1, 20))

    topic = data[0]['argument'] if data else "General Debate Topic"
    content.append(Paragraph(f"<b>Topic:</b> {topic}", styles['Normal']))
    content.append(Spacer(1, 15))

    scores_A = []
    scores_B = []

    # ---------------- ANALYSIS SECTION ----------------
    content.append(Paragraph("<b>Argument Analysis</b>", styles['Heading2']))
    content.append(Spacer(1, 10))

    def extract_score(feedback):
        match = re.search(r'(\d+)/10', feedback)
        return int(match.group(1)) if match else 5

    for i, item in enumerate(data):
        speaker = "Person 1" if i % 2 == 0 else "Person 2"
        feedback = item['feedback']
        score = extract_score(feedback)

        if speaker == "Person 1":
            scores_A.append(score)
        else:
            scores_B.append(score)

        content.append(Paragraph(f"<b>{speaker} Argument:</b> {item['argument']}", styles['Normal']))
        content.append(Spacer(1, 6))

        content.append(Paragraph(f"<b>Argument Strength:</b> {score}/10", styles['Normal']))
        content.append(Spacer(1, 5))

        # Extract structured parts
        lines = feedback.split("\n")

        content.append(Paragraph("<b>Logical Fallacies:</b>", styles['Normal']))
        for line in lines:
            if "fall" in line.lower():
                content.append(Paragraph(line, styles['Normal']))
        content.append(Spacer(1, 5))

        content.append(Paragraph("<b>Improvement Suggestions:</b>", styles['Normal']))
        for line in lines:
            if "suggest" in line.lower():
                content.append(Paragraph(line, styles['Normal']))
        content.append(Spacer(1, 10))

    # ---------------- DEBATE CONVERSATION ----------------
    content.append(Paragraph("<b>Debate Conversation</b>", styles['Heading2']))
    content.append(Spacer(1, 10))

    content.append(Paragraph(
        "Moderator: Welcome to today's debate session. Let's begin.",
        styles['Normal']))
    content.append(Spacer(1, 8))

    for i, item in enumerate(data):
        speaker = "Person 1" if i % 2 == 0 else "Person 2"
        content.append(Paragraph(f"<b>{speaker}:</b> {item['argument']}", styles['Normal']))
        content.append(Spacer(1, 6))

    content.append(Paragraph(
        "Moderator: Thank you both for your arguments. The debate is concluded.",
        styles['Normal']))
    content.append(Spacer(1, 15))

    # ---------------- BAR GRAPH ----------------
    labels = ["Person 1", "Person 2"]
    avg_A = sum(scores_A)/len(scores_A) if scores_A else 0
    avg_B = sum(scores_B)/len(scores_B) if scores_B else 0

    plt.figure(figsize=(6,3))
    plt.bar(labels, [avg_A, avg_B], color=['blue', 'orange'])
    plt.title("Average Argument Strength")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.savefig("bar.png")
    plt.close()

    content.append(Paragraph("<b>Performance Comparison (Bar Graph)</b>", styles['Heading2']))
    content.append(Spacer(1, 10))
    content.append(Image("bar.png", width=400, height=200))
    content.append(Spacer(1, 15))

    # ---------------- PIE CHART ----------------
    if avg_A > 0 or avg_B > 0:
        plt.figure()
        plt.pie(
            [avg_A, avg_B],
            labels=["Person 1", "Person 2"],
            autopct='%1.1f%%'
        )
        plt.title("Contribution Comparison")
        plt.savefig("pie.png")
        plt.close()

        content.append(Paragraph("<b>Contribution Distribution (Pie Chart)</b>", styles['Heading2']))
        content.append(Spacer(1, 10))
        content.append(Image("pie.png", width=400, height=200))
        content.append(Spacer(1, 15))

    # ---------------- CONCLUSION ----------------
    winner = "Person 1" if avg_A > avg_B else "Person 2"

    content.append(Paragraph("<b>Conclusion</b>", styles['Heading2']))
    content.append(Spacer(1, 10))

    content.append(Paragraph(
        f"Based on the analysis of argument strength, logical consistency, and clarity, {winner} performed better overall in this debate.",
        styles['Normal']))

    doc.build(content)
    return file_path
# ---------------- INPUT SECTION ----------------
st.subheader("🎤 Enter Your Debate Argument")

argument = st.text_area("Type your argument here...", height=150, placeholder="Enter a clear argument with reason...")

col1, col2 = st.columns([1,1])

with col1:
    analyze_btn = st.button("Analyze Argument")

with col2:
    generate_btn = st.button("Generate PDF Report")

# ---------------- ANALYSIS ----------------
if analyze_btn:
    if argument.strip() != "":
        with st.spinner("Analyzing..."):
            feedback = get_ai_feedback(argument)

            st.session_state.history.append({
                "argument": argument,
                "feedback": feedback
            })

            st.success("Analysis Complete!")

    else:
        st.warning("Please enter an argument!")

# ---------------- DISPLAY RESULTS ----------------
st.subheader("📊 Feedback History")

for item in reversed(st.session_state.history):
   with st.expander("🔍 View Analysis"):
    
    st.markdown('<div class="highlight-title">🧠 Argument</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="argument-box">{item["argument"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="highlight-title">📊 Feedback</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="feedback-box">{item["feedback"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
# ---------------- PDF GENERATION ----------------
if generate_btn:
    if len(st.session_state.history) > 0:
        pdf_file = generate_pdf(st.session_state.history)

        with open(pdf_file, "rb") as f:
            st.download_button(
                label="📄 Download Report",
                data=f,
                file_name="debate_report.pdf",
                mime="application/pdf"
            )
    else:
        st.warning("No data to generate report!")

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("💡 Built with Streamlit + Groq + LLaMA 3.1")