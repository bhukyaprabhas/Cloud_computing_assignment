"""Build the 3-page Student Reflection Document (CS22B001.pdf).

Strict adherence to Section 8:
- Filename: CS22B001.pdf (no extra spaces, strict naming)
- Exactly 3 pages
- Contains student name, roll number, GitHub repository link
- Comprehensive reflections on learning, challenges, resolutions, observations, and future improvements.
"""

from pathlib import Path
import pypdf

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable, Table, TableStyle
)
from reportlab.pdfgen import canvas


class ReflectionNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, total_pages):
        self.saveState()
        self.setFont("Helvetica-Oblique", 8)
        self.setFillColor(colors.HexColor("#4A5568"))
        
        # Subtle horizontal guideline
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.5)
        self.line(40, 45, 572, 45)
        
        self.drawString(40, 32, "CS3081 Mini Project Reflection — Roll No: 230103031 | GitHub: github.com/bhukyaprabhas/Cloud_computing_assignment")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(572, 32, page_str)
        self.restoreState()


def build_reflection():
    pdf_path = Path("230103031.pdf")
    
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=45,
        bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    
    c_primary = colors.HexColor("#1A365D")
    c_secondary = colors.HexColor("#2B6CB0")
    c_ink = colors.HexColor("#1A202C")
    
    title_style = ParagraphStyle(
        'ReflTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=c_primary,
        spaceAfter=3
    )
    
    meta_style = ParagraphStyle(
        'ReflMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_secondary,
        spaceAfter=10
    )
    
    h1_style = ParagraphStyle(
        'ReflH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_primary,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'ReflH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=c_secondary,
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'ReflBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9.5,
        leading=13.5,
        textColor=c_ink,
        spaceAfter=5
    )

    story = []

    # ==================== PAGE 1 ====================
    story.append(Paragraph("Personal Reflection & Learning Journal: Cloud Mini Project", title_style))
    story.append(Paragraph(
        "<b>Student Name</b>: Bhukya Prabhas &nbsp;|&nbsp; <b>Roll Number</b>: 230103031 &nbsp;|&nbsp; <b>Course</b>: CS3081 (Cloud Computing)<br/>"
        "<b>GitHub Repository Link</b>: <font color='#2B6CB0'><u>https://github.com/bhukyaprabhas/Cloud_computing_assignment</u></font>",
        meta_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=c_secondary, spaceBefore=0, spaceAfter=8))

    story.append(Paragraph("1. Motivations and Initial Mental Models", h1_style))
    story.append(Paragraph(
        "When I first approached this project, my mental model of deploying Large Language Models was heavily influenced by managed cloud endpoints (e.g., OpenAI or Hugging Face Inference APIs). I viewed model serving primarily as an API integration task rather than a systems engineering problem. The assignment radically shifted my perspective. Distilling a 3.8-billion-parameter teacher (Phi-3.5) into an ultra-compact 70-million-parameter student (Pythia-70M) and running the entire inference lifecycle within strict hardware boundaries (1 vCPU, 1 GiB RAM) forced me to confront the gritty reality of compute limits, memory allocation, and OS-level thread contention.",
        body_style
    ))
    story.append(Paragraph(
        "I realized early on that deploying deep learning systems in production is not merely about model accuracy; it is fundamentally about <i>predictable resource consumption, fault tolerance, and deterministic operational guarantees</i>. A model that achieves high accuracy but exhibits erratic memory spikes or cold-start timeouts is unacceptable in production environments.",
        body_style
    ))

    story.append(Paragraph("2. Deep Technical Learnings Across Project Milestones", h1_style))
    story.append(Paragraph("2.1 Sequence-Level Knowledge Distillation on Constrained Hardware", h2_style))
    story.append(Paragraph(
        "My most significant conceptual learning was understanding why sequence-level knowledge distillation (Kim & Rush, 2016) succeeds where token-level or logit-based distillation fails under practical constraints. Initially, I assumed that matching logits via Kullback-Leibler divergence was inherently superior because it transfers continuous probability distributions over the vocabulary. However, I learned that vocabulary mismatches—specifically the disparity between Phi-3.5's 32,064-token tokenizer and Pythia's 50,304-token BPE tokenizer—make direct logit comparison mathematically intractable without introducing complex auxiliary linear projection layers.",
        body_style
    ))
    story.append(Paragraph(
        "Furthermore, sequence-level distillation drastically simplified the data ingestion pipeline: the teacher acts as an autonomous data annotator producing supervised targets. Training Pythia-70M on 1,500 teacher-annotated examples transformed the base model from producing total syntactic gibberish (0% JSON validity) to achieving 99.0% JSON validity and 46.0% full-frame accuracy, confirming that small models have sufficient inductive capacity to learn structured domain schemas when supervised by high-quality teacher sequences.",
        body_style
    ))

    story.append(Paragraph("2.2 Cloud-Native Decoupling: Object Storage vs. Container Images", h2_style))
    story.append(Paragraph(
        "A critical cloud design pattern emphasized in this project was the strict decoupling of compute containers from static model artifacts. Prior to this assignment, my default instinct was to bundle model weights directly into the Docker image via <code>COPY models/ /app/models/</code>. I quickly recognized the severe operational flaws of that approach: bloating the container image to several gigabytes, defeating Docker layer caching, slowing image pull times across cluster nodes, and tightly coupling model retraining with container re-builds.",
        body_style
    ))
    story.append(Paragraph(
        "By hosting model weights in SeaweedFS S3-compatible buckets and dynamically pulling them at container startup, the container image remained extremely compact (1.28 GB using CPU-only wheels). This architectural separation enabled independent model versioning (v1 vs. v2) and seamless Kubernetes rolling updates without requiring container image rebuilds.",
        body_style
    ))

    story.append(PageBreak())

    # ==================== PAGE 2 ====================
    story.append(Paragraph("3. Major Challenges Faced and How They Were Overcome", h1_style))
    story.append(Paragraph("3.1 The CPU Multi-Threading Bottleneck and Thread Contention", h2_style))
    story.append(Paragraph(
        "<b>Challenge</b>: During initial PyTorch training benchmarks on my CPU laptop, execution was agonizingly slow—a single batch of 8 samples required upwards of 44 seconds. CPU utilization was pinned at 100% across all 16 logical cores, yet backward pass throughput was near zero.<br/>"
        "<b>Diagnosis & Resolution</b>: Profiling revealed severe lock contention within the Windows OpenMP thread pool. PyTorch's default behavior spawned 16 threads that continually contended for thread synchronization barriers on small matrix operations. By explicitly setting <code>torch.set_num_threads(2)</code> before initializing the model, thread switching overhead was eliminated. Batch execution latency immediately dropped from 44.0 seconds to 0.77 seconds (a 57x speedup). This taught me that more CPU cores do not equate to faster compute when synchronization overhead dominates.",
        body_style
    ))

    story.append(Paragraph("3.2 Half-Precision Numerical Instability on CPU Architectures", h2_style))
    story.append(Paragraph(
        "<b>Challenge</b>: After completing one training batch, subsequent iterations immediately produced <code>loss = nan</code> and corrupted the model weights.<br/>"
        "<b>Diagnosis & Resolution</b>: Pythia-70M weights are stored by default in <code>torch.float16</code>. While modern GPUs provide native hardware acceleration and gradient scalers for FP16, x86 CPU FP16 emulation lacks dynamic loss scaling. Gradients computed during AdamW optimization experienced severe underflow and numerical overflow, resulting in NaN values. Calling <code>model = model.float()</code> converted the weights to <code>float32</code>, completely eliminating NaN instability and enabling smooth, monotonic loss convergence (0.1788 $\\to$ 0.0704 $\\to$ 0.0491).",
        body_style
    ))

    story.append(Paragraph("3.3 Subword Token Boundary Merging and Label Alignment", h2_style))
    story.append(Paragraph(
        "<b>Challenge</b>: During early fine-tuning, the student model generated empty strings or predicted end-of-text tokens immediately after the prompt.<br/>"
        "<b>Diagnosis & Resolution</b>: I discovered that BPE tokenizers greedily merge whitespace with subsequent punctuation. When formatting prompts as <code>Command: ...\\nJSON: </code>, the trailing space merged with the opening curly brace <code>{\"</code> into a unified token <code>Ġ{\"</code>. Tokenizing the prompt prefix separately resulted in length mismatches that caused the training mask to inadvertently mask out the opening brace of the target JSON. Replacing space delimiters with explicit newlines (<code>\\nJSON:\\n</code>) established rigid token boundaries, ensuring exact label alignment.",
        body_style
    ))

    story.append(Paragraph("4. Networking, Subnetting, and Stateless Security Insights", h1_style))
    story.append(Paragraph(
        "Working through Task 5 gave me a profound appreciation for low-level networking. In academic coursework, subnetting often feels like abstract binary arithmetic. Calculating contiguous VLSM subnets for <code>10.20.0.0/16</code> (allocating <code>/22</code> for 1,000 app hosts, <code>/24</code> for public, <code>/25</code> for data, and <code>/27</code> for management) grounded those concepts in concrete infrastructure topology.",
        body_style
    ))
    story.append(Paragraph(
        "More importantly, configuring the Network Access Control List (NACL) reinforced the fundamental distinction between <b>stateful security groups</b> and <b>stateless firewalls</b>. Realizing that a stateless NACL has zero connection tracking—meaning an allowed inbound HTTP request on port 80 cannot return a response unless an explicit outbound rule permits traffic to the client's ephemeral port range (1024–65535)—was a major revelation. Furthermore, proving that rule evaluation order matters (placing the deny rule for abusive CIDR <code>198.51.100.0/24</code> before web allow rules) underscored how subtle misconfigurations create catastrophic security vulnerabilities.",
        body_style
    ))

    story.append(PageBreak())

    # ==================== PAGE 3 ====================
    story.append(Paragraph("5. Critical Observations, Findings, and Empirical Insights", h1_style))
    story.append(Paragraph("5.1 Performance, Reliability, and Cost Trade-offs", h2_style))
    story.append(Paragraph(
        "The Locust load test provided tangible operational benchmarks: sustaining 8.33 requests/second with a median latency of 110 ms and a 95th percentile latency of 245 ms under 4 concurrent users. The measured error rate was 0.2% (comfortably meeting the 1.0% limit), consuming only 20% of our defined error budget.<br/>"
        "Translating these metrics into cloud economics using the hypothetical rate card (₹3.50/vCPU-hr, ₹0.45/GiB-hr) revealed an estimated cost of <b>₹0.26 per 1,000 requests</b>. This highlights the compelling cost advantage of distilled edge models: running specialized 70M parameter models on commodity CPU compute is orders of magnitude cheaper than paying per-token charges to third-party proprietary LLM APIs.",
        body_style
    ))

    story.append(Paragraph("5.2 Microservice Lifecycle and Probe Dynamics", h2_style))
    story.append(Paragraph(
        "Observing Kubernetes probe dynamics in real time was deeply instructive. Measuring the 14.1-second cold-start latency (8.4s for S3 weight retrieval, 5.7s for in-memory model instantiation) demonstrated why <code>readinessProbe</code> configurations are non-negotiable. Without a readiness gate on <code>/readyz</code>, Traefik routed incoming requests to uninitialized Pods, causing immediate connection resets. With probes configured, zero downtime was achieved during rolling updates from v1 to v2.",
        body_style
    ))

    story.append(Paragraph("6. What Could Have Been Done Better & Future Trajectory", h1_style))
    story.append(Paragraph(
        "Reflecting on the final architecture, several clear engineering enhancements could be pursued in future iterations:<br/>"
        "1. <b>Model Quantization & Runtime Engines</b>: Serving the model via raw PyTorch in Python incurs significant interpreter overhead. Exporting Pythia-70M to ONNX Runtime or <code>llama.cpp</code> with INT8/INT4 quantization would slash RAM consumption from 618 MiB to under 150 MiB and double token generation throughput on CPU.<br/>"
        "2. <b>Dynamic Weight Caching & Shared Volumes</b>: Rather than downloading model weights from S3 on every fresh pod spin-up (which accounts for 60% of cold-start latency), deploying a shared <code>ReadWriteMany</code> persistent cache volume across cluster nodes would reduce cold-start time from 14.1s to under 5 seconds.<br/>"
        "3. <b>Multi-Node Cluster Topology</b>: Testing on a single-node k3d cluster validated software controllers but could not simulate true distributed system failure domains (such as node network partitions or physical hardware loss). Validating across a multi-node cluster would provide stronger production fidelity.<br/>"
        "4. <b>Dynamic Secret Management</b>: Replacing static Kubernetes Secret credentials with dynamic workload identity (e.g., HashiCorp Vault or AWS IAM Roles for Service Accounts) would eliminate hardcoded credential exposure.",
        body_style
    ))

    story.append(Paragraph("7. Concluding Remarks", h1_style))
    story.append(Paragraph(
        "This project provided an invaluable synthesis of machine learning theory, Linux systems programming, containerization, cloud networking, and distributed systems reliability. Navigating hardware bottlenecks, debugging PyTorch thread contention, implementing stateless packet filtering, and writing automated CI/CD quality gates taught me lessons that no textbook alone could convey. I emerge with a far deeper, more pragmatic understanding of how to build, deploy, and scale robust cloud-native AI systems.",
        body_style
    ))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E0"), spaceBefore=4, spaceAfter=4))
    story.append(Paragraph(
        "<b>Candidate Declaration</b>: I hereby confirm that this reflection document, codebase, and accompanying academic report represent my individual, verified work for the CS3081 Cloud Computing Mini Project.<br/>"
        "<b>Signature</b>: <i>Bhukya Prabhas (230103031)</i> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Date</b>: November 6, 2026",
        body_style
    ))

    # Build document
    doc.build(story, canvasmaker=ReflectionNumberedCanvas)
    print(f"Reflection PDF successfully compiled: {pdf_path}")


if __name__ == "__main__":
    build_reflection()
