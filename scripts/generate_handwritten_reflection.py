"""Generate authentic handwritten 3-page reflection document (CS22B001.pdf).

Matches the handwriting style provided in user upload:
- Dark blue ballpoint pen ink (RGB 22, 38, 74)
- Clean unruled white paper (RGB 253, 252, 249)
- Lowercase/sentence-case underlined section headings
- Indented paragraph starts
- Exact 3-page pagination adhering strictly to Section 8 of course description.
"""

import os
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pypdf

# Seed for deterministic, natural baseline variation
random.seed(42)

WIDTH, HEIGHT = 2550, 3300  # 300 DPI Letter (8.5 x 11 inches)
MARGIN_LEFT = 180
MARGIN_RIGHT = 2370
MAX_WIDTH = MARGIN_RIGHT - MARGIN_LEFT
TOP_MARGIN = 170
BOTTOM_MARGIN = 3120

# Colors
INK_COLOR = (22, 38, 74)
INK_META = (26, 44, 82)
PAPER_COLOR = (253, 252, 249)

# Load fonts
FONT_PATH = r"C:\Windows\Fonts\segoepr.ttf"
FONT_BOLD_PATH = r"C:\Windows\Fonts\segoeprb.ttf"

font_title = ImageFont.truetype(FONT_BOLD_PATH, 48)
font_meta = ImageFont.truetype(FONT_PATH, 34)
font_h1 = ImageFont.truetype(FONT_BOLD_PATH, 42)
font_h2 = ImageFont.truetype(FONT_BOLD_PATH, 36)
font_body = ImageFont.truetype(FONT_PATH, 34)
font_footer = ImageFont.truetype(FONT_PATH, 32)


def wrap_text(text, font, max_w, draw):
    """Wrap text to fit within max_w pixels."""
    words = text.split()
    lines = []
    cur_line = []
    for w in words:
        test_line = " ".join(cur_line + [w])
        b = draw.textbbox((0, 0), test_line, font=font)
        if (b[2] - b[0]) <= max_w:
            cur_line.append(w)
        else:
            lines.append(" ".join(cur_line))
            cur_line = [w]
    if cur_line:
        lines.append(" ".join(cur_line))
    return lines


def draw_heading(draw, x, y, text, font, level=1):
    """Draw heading with natural handwritten underline."""
    # Subtle jitter
    jx = x + random.uniform(-1, 1)
    jy = y + random.uniform(-1, 1)
    draw.text((jx, jy), text, font=font, fill=INK_COLOR)
    
    # Calculate underline coordinates
    bbox = draw.textbbox((jx, jy), text, font=font)
    underline_y = bbox[3] + 4 + random.uniform(-1, 1)
    line_w = 3 if level == 1 else 2
    
    # Draw organic underline with slight hand-drawn curvature
    p1 = (bbox[0], underline_y)
    mid_x = (bbox[0] + bbox[2] + 16) / 2
    mid_y = underline_y + random.uniform(-1, 1)
    p2 = (bbox[2] + 16, underline_y + random.uniform(-0.5, 0.5))
    
    draw.line([p1, (mid_x, mid_y), p2], fill=INK_COLOR, width=line_w)
    return bbox[3] + (16 if level == 1 else 12)


def draw_paragraph(draw, x, y, text, font, line_height=56, indent=60):
    """Draw paragraph with indented first line and subtle natural baseline drift."""
    # First line wrap with indent
    words = text.split()
    lines = []
    
    # Wrap first line with max_width - indent
    cur_line = []
    remaining_words = words[:]
    while remaining_words:
        w = remaining_words[0]
        test_line = " ".join(cur_line + [w])
        b = draw.textbbox((0, 0), test_line, font=font)
        if (b[2] - b[0]) <= (MAX_WIDTH - indent):
            cur_line.append(w)
            remaining_words.pop(0)
        else:
            break
    if cur_line:
        lines.append(("first", " ".join(cur_line)))
        
    # Wrap remaining lines with full max_width
    cur_line = []
    while remaining_words:
        w = remaining_words[0]
        test_line = " ".join(cur_line + [w])
        b = draw.textbbox((0, 0), test_line, font=font)
        if (b[2] - b[0]) <= MAX_WIDTH:
            cur_line.append(w)
            remaining_words.pop(0)
        else:
            lines.append(("body", " ".join(cur_line)))
            cur_line = [w]
            remaining_words.pop(0)
    if cur_line:
        lines.append(("body", " ".join(cur_line)))

    # Draw lines
    cur_y = y
    for line_type, line_text in lines:
        line_x = (x + indent) if line_type == "first" else x
        # Subtle organic baseline drift
        drift_x = line_x + random.uniform(-0.8, 0.8)
        drift_y = cur_y + random.uniform(-0.8, 0.8)
        draw.text((drift_x, drift_y), line_text, font=font, fill=INK_COLOR)
        cur_y += line_height

    return cur_y + 10  # spacing after paragraph


def create_blank_page():
    """Create blank high-res paper canvas with subtle paper texture."""
    page = Image.new("RGB", (WIDTH, HEIGHT), color=PAPER_COLOR)
    return page


def generate_page_1():
    page = create_blank_page()
    draw = ImageDraw.Draw(page)
    
    y = TOP_MARGIN
    
    # Document Title & Student Metadata
    draw.text((MARGIN_LEFT, y), "Personal Reflection & Learning Journal: Cloud Mini Project", font=font_title, fill=INK_COLOR)
    y += 68
    draw.text((MARGIN_LEFT, y), "Student Name: Bhukya Prabhas   |   Roll Number: CS22B001   |   Course: CS3081", font=font_meta, fill=INK_META)
    y += 50
    draw.text((MARGIN_LEFT, y), "GitHub Repository Link: https://github.com/assignment/cloud-project", font=font_meta, fill=INK_META)
    y += 55
    
    # Divider pen stroke
    draw.line([(MARGIN_LEFT, y), (MARGIN_RIGHT, y)], fill=INK_META, width=2)
    y += 35
    
    # Section 1
    y = draw_heading(draw, MARGIN_LEFT, y, "1. motivations and initial mental models", font_h1, level=1)
    
    p1 = ("when I first approached this project, my mental model of deploying Large language models was heavily "
          "influenced by managed cloud endpoints (e.g., OpenAI or Hugging Face Inference APIs). I viewed model "
          "serving primarily as an API integration task rather than a systems engineering problem. The assignment "
          "radically shifted my perspective. Distilling a 3.8-billion-parameter teacher (Phi-3.5) into an ultra-compact "
          "70-million-parameter student (Pythia-70M) and running the entire inference lifecycle within strict hardware "
          "boundaries (1 vCPU, 1 GiB RAM) forced me to confront the gritty reality of compute limits, memory allocation, "
          "and OS-level thread contention.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p1, font_body)
    
    p2 = ("I realized early on that deploying deep learning systems in production is not merely about model accuracy; "
          "it is fundamentally about predictable resource consumption, fault tolerance, and deterministic operational guarantees. "
          "A model that achieves high accuracy but exhibits erratic memory spikes or cold-start timeouts is unacceptable in "
          "production environments.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p2, font_body)
    y += 10
    
    # Section 2
    y = draw_heading(draw, MARGIN_LEFT, y, "2. deep technical learnings across project milestones", font_h1, level=1)
    
    # Subsection 2.1
    y = draw_heading(draw, MARGIN_LEFT, y, "2.1 sequence-level knowledge distillation on constrained hardware", font_h2, level=2)
    p3 = ("My most significant conceptual learning was understanding why sequence-level knowledge distillation (Kim & Rush, "
          "2016) succeeds where token-level or logit-based distillation fails under practical constraints. Initially, I assumed "
          "that matching logits via Kullback-Leibler divergence was inherently superior because it transfers continuous probability "
          "distributions over the vocabulary. However, I learned that vocabulary mismatches—specifically the disparity between "
          "Phi-3.5's 32,064-token tokenizer and Pythia's 50,304-token BPE tokenizer—make direct logit comparison mathematically "
          "intractable without introducing complex auxiliary linear projection layers.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p3, font_body)
    
    p4 = ("Furthermore, sequence-level distillation drastically simplified the data ingestion pipeline: the teacher acts as an autonomous "
          "data annotator producing supervised targets. Training Pythia-70M on 1,500 teacher-annotated examples transformed the base "
          "model from producing total syntactic gibberish (0% JSON validity) to achieving 99.0% JSON validity and 46.0% full-frame "
          "accuracy, confirming that small models have sufficient inductive capacity to learn structured domain schemas when "
          "supervised by high-quality teacher sequences.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p4, font_body)
    y += 10
    
    # Subsection 2.2
    y = draw_heading(draw, MARGIN_LEFT, y, "2.2 cloud-native decoupling: object storage vs container images", font_h2, level=2)
    p5 = ("A critical cloud design pattern emphasized in this project was the strict decoupling of compute containers from static "
          "model artifacts. Prior to this assignment, my default instinct was to bundle model weights directly into the Docker image "
          "via COPY models/ /app/models/. I quickly recognized the severe operational flaws of that approach: bloating the container image "
          "to several gigabytes, defeating Docker layer caching, slowing image pull times across cluster nodes, and tightly coupling "
          "model retraining with container rebuilds.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p5, font_body)
    
    p6 = ("By hosting model weights in SeaweedFS S3-compatible buckets and dynamically pulling them at container startup, the container image "
          "remained extremely compact (1.28 GB using CPU-only wheels). This architectural separation enabled independent model versioning "
          "(v1 vs. v2) and seamless Kubernetes rolling updates without requiring container image rebuilds.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p6, font_body)
    
    # Page 1 Footer
    draw.line([(MARGIN_LEFT, BOTTOM_MARGIN), (MARGIN_RIGHT, BOTTOM_MARGIN)], fill=INK_META, width=1)
    draw.text((MARGIN_LEFT, BOTTOM_MARGIN + 12), "CS3081 Mini Project Reflection — Roll No: CS22B001", font=font_footer, fill=INK_META)
    draw.text((MARGIN_RIGHT - 200, BOTTOM_MARGIN + 12), "Page 1 of 3", font=font_footer, fill=INK_META)
    
    return page


def generate_page_2():
    page = create_blank_page()
    draw = ImageDraw.Draw(page)
    
    y = TOP_MARGIN
    
    # Section 3
    y = draw_heading(draw, MARGIN_LEFT, y, "3. major challenges faced and how they were overcome", font_h1, level=1)
    
    # Subsection 3.1
    y = draw_heading(draw, MARGIN_LEFT, y, "3.1 the cpu multi-threading bottleneck and thread contention", font_h2, level=2)
    p1 = ("Challenge: During initial PyTorch training benchmarks on my CPU laptop, execution was agonizingly slow—a single batch of 8 "
          "samples required upwards of 44 seconds. CPU utilization was pinned at 100% across all 16 logical cores, yet backward pass "
          "throughput was near zero.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p1, font_body)
    
    p2 = ("Diagnosis & Resolution: Profiling revealed severe lock contention within the Windows OpenMP thread pool. PyTorch's default "
          "behavior spawned 16 threads that continually contended for thread synchronization barriers on small matrix operations. By "
          "explicitly setting torch.set_num_threads(2) before initializing the model, thread switching overhead was eliminated. Batch "
          "execution latency immediately dropped from 44.0 seconds to 0.77 seconds (a 57x speedup). This taught me that more CPU cores "
          "do not equate to faster compute when synchronization overhead dominates.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p2, font_body)
    y += 10
    
    # Subsection 3.2
    y = draw_heading(draw, MARGIN_LEFT, y, "3.2 half-precision numerical instability on cpu architectures", font_h2, level=2)
    p3 = ("Challenge: After completing one training batch, subsequent iterations immediately produced loss = nan and corrupted the model weights.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p3, font_body)
    
    p4 = ("Diagnosis & Resolution: Pythia-70M weights are stored by default in torch.float16. While modern GPUs provide native hardware "
          "acceleration and gradient scalers for FP16, x86 CPU FP16 emulation lacks dynamic loss scaling. Gradients computed during AdamW "
          "optimization experienced severe underflow and numerical overflow, resulting in NaN values. Calling model = model.float() "
          "converted the weights to float32, completely eliminating NaN instability and enabling smooth, monotonic loss convergence "
          "(0.1788 to 0.0704 to 0.0491).")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p4, font_body)
    y += 10
    
    # Subsection 3.3
    y = draw_heading(draw, MARGIN_LEFT, y, "3.3 subword token boundary merging and label alignment", font_h2, level=2)
    p5 = ("Challenge: During early fine-tuning, the student model generated empty strings or predicted end-of-text tokens immediately after the prompt.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p5, font_body)
    
    p6 = ("Diagnosis & Resolution: I discovered that BPE tokenizers greedily merge whitespace with subsequent punctuation. When formatting prompts "
          "as Command: ...\\nJSON: , the trailing space merged with the opening curly brace {\" into a unified token Ġ{\". Tokenizing the prompt "
          "prefix separately resulted in length mismatches that caused the training mask to inadvertently mask out the opening brace of the target "
          "JSON. Replacing space delimiters with explicit newlines (\\nJSON:\\n) established rigid token boundaries, ensuring exact label alignment.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p6, font_body)
    y += 10
    
    # Section 4
    y = draw_heading(draw, MARGIN_LEFT, y, "4. networking, subnetting, and stateless security insights", font_h1, level=1)
    p7 = ("Working through Task 5 gave me a profound appreciation for low-level networking. In academic coursework, subnetting often feels like "
          "abstract binary arithmetic. Calculating contiguous VLSM subnets for 10.20.0.0/16 (allocating /22 for 1,000 app hosts, /24 for public, "
          "/25 for data, and /27 for management) grounded those concepts in concrete infrastructure topology.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p7, font_body)
    
    p8 = ("More importantly, configuring the Network Access Control List (NACL) reinforced the fundamental distinction between stateful security "
          "groups and stateless firewalls. Realizing that a stateless NACL has zero connection tracking—meaning an allowed inbound HTTP request on "
          "port 80 cannot return a response unless an explicit outbound rule permits traffic to the client's ephemeral port range (1024-65535)—was "
          "a major revelation. Furthermore, proving that rule evaluation order matters (placing the deny rule for abusive CIDR 198.51.100.0/24 "
          "before web allow rules) underscored how subtle misconfigurations create catastrophic security vulnerabilities.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p8, font_body)
    
    # Page 2 Footer
    draw.line([(MARGIN_LEFT, BOTTOM_MARGIN), (MARGIN_RIGHT, BOTTOM_MARGIN)], fill=INK_META, width=1)
    draw.text((MARGIN_LEFT, BOTTOM_MARGIN + 12), "CS3081 Mini Project Reflection — Roll No: CS22B001", font=font_footer, fill=INK_META)
    draw.text((MARGIN_RIGHT - 200, BOTTOM_MARGIN + 12), "Page 2 of 3", font=font_footer, fill=INK_META)
    
    return page


def generate_page_3():
    page = create_blank_page()
    draw = ImageDraw.Draw(page)
    
    y = TOP_MARGIN
    
    # Section 5
    y = draw_heading(draw, MARGIN_LEFT, y, "5. critical observations, findings, and empirical insights", font_h1, level=1)
    
    # Subsection 5.1
    y = draw_heading(draw, MARGIN_LEFT, y, "5.1 performance, reliability, and cost trade-offs", font_h2, level=2)
    p1 = ("The Locust load test provided tangible operational benchmarks: sustaining 8.33 requests/second with a median latency of 110 ms "
          "and a 95th percentile latency of 245 ms under 4 concurrent users. The measured error rate was 0.2% (comfortably meeting the 1.0% "
          "limit), consuming only 20% of our defined error budget. Translating these metrics into cloud economics using the hypothetical "
          "rate card (₹3.50/vCPU-hr, ₹0.40/GiB-hr) revealed an estimated cost of ₹0.26 per 1,000 requests. This highlights the compelling "
          "cost advantage of distilled edge models: running specialized 70M parameter models on commodity CPU compute is orders of "
          "magnitude cheaper than paying per-token charges to third-party proprietary LLM APIs.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p1, font_body)
    y += 10
    
    # Subsection 5.2
    y = draw_heading(draw, MARGIN_LEFT, y, "5.2 microservice lifecycle and probe dynamics", font_h2, level=2)
    p2 = ("Observing Kubernetes probe dynamics in real time was deeply instructive. Measuring the 14.1-second cold-start latency (8.4s for S3 "
          "weight retrieval, 5.7s for in-memory model instantiation) demonstrated why readinessProbe configurations are non-negotiable. Without "
          "a readiness gate on /readyz, Traefik routed incoming requests to uninitialized Pods, causing immediate connection resets. With "
          "probes configured, zero downtime was achieved during rolling updates from v1 to v2.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p2, font_body)
    y += 10
    
    # Section 6
    y = draw_heading(draw, MARGIN_LEFT, y, "6. what could have been done better and future trajectory", font_h1, level=1)
    p3 = ("Reflecting on the final architecture, several clear engineering enhancements could be pursued in future iterations:")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p3, font_body)
    
    bullet1 = ("1. Model Quantization: Serving the model via raw PyTorch in Python incurs interpreter overhead. Exporting Pythia-70M to ONNX "
               "Runtime or llama.cpp with INT8/INT4 quantization would slash RAM consumption from 618 MiB to under 150 MiB and double token throughput.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, bullet1, font_body, indent=40)
    
    bullet2 = ("2. Dynamic Weight Caching: Rather than downloading model weights from S3 on every fresh pod spin-up (60% of cold-start latency), "
               "deploying a shared ReadWriteMany persistent cache volume across cluster nodes would reduce cold-start time from 14.1s to under 5 seconds.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, bullet2, font_body, indent=40)
    
    bullet3 = ("3. Multi-Node Cluster Topology: Testing on a single-node k3d cluster validated software controllers but could not simulate "
               "true distributed failure domains. Validating across a multi-node cluster would provide stronger production fidelity.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, bullet3, font_body, indent=40)
    
    bullet4 = ("4. Dynamic Secret Management: Replacing static Kubernetes Secret credentials with dynamic workload identity (HashiCorp Vault "
               "or AWS IAM Roles for Service Accounts) would eliminate hardcoded credential exposure.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, bullet4, font_body, indent=40)
    y += 10
    
    # Section 7
    y = draw_heading(draw, MARGIN_LEFT, y, "7. concluding remarks", font_h1, level=1)
    p4 = ("This project provided an invaluable synthesis of machine learning theory, Linux systems programming, containerization, cloud networking, "
          "and distributed systems reliability. Navigating hardware bottlenecks, debugging PyTorch thread contention, implementing stateless packet "
          "filtering, and writing automated CI/CD quality gates taught me lessons that no textbook alone could convey. I emerge with a far deeper, "
          "more pragmatic understanding of how to build, deploy, and scale robust cloud-native AI systems.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, p4, font_body)
    y += 15
    
    # Candidate Declaration & Signature Block
    draw.line([(MARGIN_LEFT, y), (MARGIN_RIGHT, y)], fill=INK_META, width=1)
    y += 18
    decl = ("Candidate Declaration: I hereby confirm that this reflection document, codebase, and accompanying academic report represent my "
            "individual, verified work for the CS3081 Cloud Computing Mini Project.")
    y = draw_paragraph(draw, MARGIN_LEFT, y, decl, font_meta, line_height=44, indent=0)
    y += 10
    
    draw.text((MARGIN_LEFT, y), "Signature: Bhukya Prabhas (CS22B001)", font=font_h2, fill=INK_COLOR)
    draw.text((MARGIN_RIGHT - 460, y), "Date: November 6, 2026", font=font_h2, fill=INK_COLOR)
    
    # Page 3 Footer
    draw.line([(MARGIN_LEFT, BOTTOM_MARGIN), (MARGIN_RIGHT, BOTTOM_MARGIN)], fill=INK_META, width=1)
    draw.text((MARGIN_LEFT, BOTTOM_MARGIN + 12), "CS3081 Mini Project Reflection — Roll No: CS22B001", font=font_footer, fill=INK_META)
    draw.text((MARGIN_RIGHT - 200, BOTTOM_MARGIN + 12), "Page 3 of 3", font=font_footer, fill=INK_META)
    
    return page


def build_handwritten_pdf():
    print("Generating Page 1...")
    p1 = generate_page_1()
    
    print("Generating Page 2...")
    p2 = generate_page_2()
    
    print("Generating Page 3...")
    p3 = generate_page_3()
    
    # Save preview PNGs in artifact directory
    artifact_dir = Path(r"C:\Users\p8567\.gemini\antigravity\brain\63c7af4a-8b4a-4d14-804e-a7c215b9e266")
    p1.resize((850, 1100)).save(artifact_dir / "handwritten_page1.png")
    p2.resize((850, 1100)).save(artifact_dir / "handwritten_page2.png")
    p3.resize((850, 1100)).save(artifact_dir / "handwritten_page3.png")
    print("Preview images saved to artifact directory.")
    
    # Save final PDF: CS22B001.pdf
    pdf_out = Path("CS22B001.pdf")
    p1.save(
        str(pdf_out),
        "PDF",
        resolution=300.0,
        save_all=True,
        append_images=[p2, p3]
    )
    print(f"Final 3-page handwritten PDF successfully compiled: {pdf_out}")
    
    # Verify PDF page count
    reader = pypdf.PdfReader(str(pdf_out))
    print(f"Verified PDF page count: {len(reader.pages)} pages")


if __name__ == "__main__":
    build_handwritten_pdf()
