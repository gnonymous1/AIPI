// ═══════════════════════════════════════════════════════════════
//  PROVIDER HUB — Complete 169+ Provider Manager & Hub
// ═══════════════════════════════════════════════════════════════

var HUB_PROVIDER_META = {
    // Cloud Giants & Major Labs
    "OpenAI":                        { emoji: "🟢", color: "#10a37f", authType: "apikey", keyHint: "sk-proj-...", category: "cloud", defaultUrl: "https://api.openai.com/v1", defaultModel: "gpt-4o" },
    "Google Antigravity":            { emoji: "🚀", color: "#4285f4", authType: "oauth-antigravity", keyHint: "1-Click Google OAuth", category: "cloud", defaultUrl: "https://cloudcode-pa.googleapis.com", defaultModel: "antigravity/claude-sonnet-4-6" },
    "Anthropic":                     { emoji: "🟠", color: "#d97706", authType: "apikey", keyHint: "sk-ant-...", category: "cloud", defaultUrl: "https://api.anthropic.com/v1", defaultModel: "claude-3-7-sonnet-20250219" },
    "Google Gemini (OpenAI Compat)": { emoji: "🔵", color: "#4285f4", authType: "apikey", keyHint: "AIzaSy...", category: "cloud", defaultUrl: "https://generativelanguage.googleapis.com/v1beta/openai", defaultModel: "gemini-2.0-flash" },
    "DeepSeek AI":                   { emoji: "🐋", color: "#2563eb", authType: "apikey", keyHint: "sk-...", category: "reasoning", defaultUrl: "https://api.deepseek.com", defaultModel: "deepseek-chat" },
    "Groq Cloud":                    { emoji: "⚡", color: "#f59e0b", authType: "apikey", keyHint: "gsk_...", category: "fast", defaultUrl: "https://api.groq.com/openai/v1", defaultModel: "llama-3.3-70b-versatile" },
    "Mistral AI":                    { emoji: "🌀", color: "#7c3aed", authType: "apikey", keyHint: "...", category: "cloud", defaultUrl: "https://api.mistral.ai/v1", defaultModel: "mistral-large-latest" },
    "xAI (Grok)":                    { emoji: "✖️", color: "#6b7280", authType: "apikey", keyHint: "xai-...", category: "cloud", defaultUrl: "https://api.x.ai/v1", defaultModel: "grok-2-latest" },
    "Cohere":                        { emoji: "🟣", color: "#8b5cf6", authType: "apikey", keyHint: "...", category: "cloud", defaultUrl: "https://api.cohere.com/v2", defaultModel: "command-r-plus" },
    "Perplexity AI":                 { emoji: "🔍", color: "#06b6d4", authType: "apikey", keyHint: "pplx-...", category: "cloud", defaultUrl: "https://api.perplexity.ai", defaultModel: "sonar-pro" },
    "Cerebras Cloud":                { emoji: "🧠", color: "#ec4899", authType: "apikey", keyHint: "csk-...", category: "fast", defaultUrl: "https://api.cerebras.ai/v1", defaultModel: "llama3.3-70b" },
    "SambaNova Cloud":               { emoji: "⚙️", color: "#f97316", authType: "apikey", keyHint: "...", category: "fast", defaultUrl: "https://api.sambanova.ai/v1", defaultModel: "Meta-Llama-3.3-70B-Instruct" },
    "Together AI":                   { emoji: "🤝", color: "#3b82f6", authType: "apikey", keyHint: "...", category: "fast", defaultUrl: "https://api.together.xyz/v1", defaultModel: "meta-llama/Llama-3.3-70B-Instruct-Turbo" },
    "Fireworks AI":                  { emoji: "🎆", color: "#e11d48", authType: "apikey", keyHint: "fw_...", category: "fast", defaultUrl: "https://api.fireworks.ai/inference/v1", defaultModel: "accounts/fireworks/models/llama-v3p3-70b-instruct" },
    "OpenRouter":                    { emoji: "🌐", color: "#0284c7", authType: "apikey", keyHint: "sk-or-v1-...", category: "router", defaultUrl: "https://openrouter.ai/api/v1", defaultModel: "auto" },
    "Novita AI":                     { emoji: "✨", color: "#8b5cf6", authType: "apikey", keyHint: "...", category: "fast", defaultUrl: "https://api.novita.ai/v3/openai", defaultModel: "meta-llama/llama-3.3-70b-instruct" },
    "Hyperbolic":                    { emoji: "🚀", color: "#d97706", authType: "apikey", keyHint: "...", category: "fast", defaultUrl: "https://api.hyperbolic.xyz/v1", defaultModel: "meta-llama/Llama-3.3-70B-Instruct" },
    "SiliconFlow (SiliconCloud)":     { emoji: "🌊", color: "#3b82f6", authType: "apikey", keyHint: "sk-...", category: "asian", defaultUrl: "https://api.siliconflow.cn/v1", defaultModel: "deepseek-ai/DeepSeek-V3" },
    "Nebius AI Studio":              { emoji: "☁️", color: "#6366f1", authType: "apikey", keyHint: "...", category: "cloud", defaultUrl: "https://api.studio.nebius.ai/v1", defaultModel: "meta-llama/Meta-Llama-3.3-70B-Instruct" },
    "DeepInfra":                     { emoji: "⚡", color: "#059669", authType: "apikey", keyHint: "...", category: "fast", defaultUrl: "https://api.deepinfra.com/v1/openai", defaultModel: "meta-llama/Llama-3.3-70B-Instruct" },
    "Anyscale Endpoints":            { emoji: "📊", color: "#0369a1", authType: "apikey", keyHint: "esecret_...", category: "cloud", defaultUrl: "https://api.endpoints.anyscale.com/v1", defaultModel: "meta-llama/Llama-3.3-70B-Instruct" },

    // Asian & International AI Leaders
    "Moonshot AI (Kimi)":            { emoji: "🌙", color: "#10b981", authType: "apikey", keyHint: "sk-...", category: "asian", defaultUrl: "https://api.moonshot.cn/v1", defaultModel: "moonshot-v1-8k" },
    "Zhipu AI (GLM)":                { emoji: "智", color: "#2563eb", authType: "apikey", keyHint: "...", category: "asian", defaultUrl: "https://open.bigmodel.cn/api/paas/v4", defaultModel: "glm-4-plus" },
    "Alibaba DashScope (Qwen)":      { emoji: "千", color: "#f97316", authType: "apikey", keyHint: "sk-...", category: "asian", defaultUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1", defaultModel: "qwen-max" },
    "Baidu Qianfan (Ernie)":         { emoji: "文", color: "#3b82f6", authType: "apikey", keyHint: "...", category: "asian", defaultUrl: "https://qianfan.baidubce.com/v2", defaultModel: "ernie-4.0-8k-latest" },
    "Tencent Hunyuan":               { emoji: "混", color: "#0ea5e9", authType: "apikey", keyHint: "...", category: "asian", defaultUrl: "https://api.hunyuan.cloud.tencent.com/v1", defaultModel: "hunyuan-pro" },
    "ByteDance Doubao (Volcengine)": { emoji: "🌋", color: "#ef4444", authType: "apikey", keyHint: "...", category: "asian", defaultUrl: "https://ark.cn-beijing.volces.com/api/v3", defaultModel: "doubao-pro-128k" },
    "01.AI (Yi)":                    { emoji: "壹", color: "#8b5cf6", authType: "apikey", keyHint: "...", category: "asian", defaultUrl: "https://api.lingyiwanwu.com/v1", defaultModel: "yi-lightning" },
    "Baichuan AI":                   { emoji: "百", color: "#14b8a6", authType: "apikey", keyHint: "...", category: "asian", defaultUrl: "https://api.baichuan-ai.com/v1", defaultModel: "Baichuan4" },
    "MiniMax":                       { emoji: "👾", color: "#f43f5e", authType: "apikey", keyHint: "...", category: "asian", defaultUrl: "https://api.minimax.chat/v1", defaultModel: "abab6.5t-chat" },
    "StepFun (Jieyue)":              { emoji: "🪜", color: "#8b5cf6", authType: "apikey", keyHint: "...", category: "asian", defaultUrl: "https://api.stepfun.com/v1", defaultModel: "step-1v-8k" },
    "Upstage AI (Solar)":            { emoji: "☀️", color: "#eab308", authType: "apikey", keyHint: "up_...", category: "asian", defaultUrl: "https://api.upstage.ai/v1/solar", defaultModel: "solar-pro" },
    "Inflection AI":                 { emoji: "π", color: "#10b981", authType: "apikey", keyHint: "...", category: "cloud", defaultUrl: "https://api.inflection.ai/v1", defaultModel: "inflection-3-pi" },
    "AI21 Labs (Jamba)":             { emoji: "🦁", color: "#6366f1", authType: "apikey", keyHint: "...", category: "cloud", defaultUrl: "https://api.ai21.com/v1", defaultModel: "jamba-1.5-large" },
    "Voyage AI":                     { emoji: "🚢", color: "#0284c7", authType: "apikey", keyHint: "pa-...", category: "cloud", defaultUrl: "https://api.voyageai.com/v1", defaultModel: "voyage-3-large" },
    "Jina AI":                       { emoji: "🔎", color: "#059669", authType: "apikey", keyHint: "jina_...", category: "cloud", defaultUrl: "https://api.jina.ai/v1", defaultModel: "jina-embeddings-v3" },
    "FriendliAI":                    { emoji: "⚡", color: "#f59e0b", authType: "apikey", keyHint: "...", category: "fast", defaultUrl: "https://inference.friendli.ai/v1", defaultModel: "meta-llama-3.3-70b-instruct" },
    "Scaleway AI Inference":         { emoji: "🇫🇷", color: "#7c3aed", authType: "apikey", keyHint: "...", category: "cloud", defaultUrl: "https://api.scaleway.com/ai-inference/v1", defaultModel: "llama-3.3-70b-instruct" },
    "OVHcloud AI Endpoints":         { emoji: "🇪🇺", color: "#0284c7", authType: "apikey", keyHint: "...", category: "cloud", defaultUrl: "https://api.ovh.com/v1/ai", defaultModel: "meta-llama-3-70b-instruct" },
    "Lepton AI":                     { emoji: "⚛️", color: "#ec4899", authType: "apikey", keyHint: "...", category: "fast", defaultUrl: "https://api.lepton.ai/v1", defaultModel: "llama3-3-70b-instruct" },
    "OctoAI (DigitalOcean)":         { emoji: "🐙", color: "#0080ff", authType: "apikey", keyHint: "...", category: "cloud", defaultUrl: "https://text.octoai.run/v1", defaultModel: "meta-llama-3.3-70b-instruct" },
    "Replicate":                     { emoji: "📦", color: "#475569", authType: "apikey", keyHint: "r8_...", category: "cloud", defaultUrl: "https://api.replicate.com/v1", defaultModel: "meta/llama-2-70b-chat" },
    "Hugging Face Inference":        { emoji: "🤗", color: "#f59e0b", authType: "apikey", keyHint: "hf_...", category: "cloud", defaultUrl: "https://api-inference.huggingface.co/v1", defaultModel: "meta-llama/Llama-3.3-70B-Instruct" },
    "Baseten":                       { emoji: "🧱", color: "#64748b", authType: "apikey", keyHint: "...", category: "cloud", defaultUrl: "https://model-baseten.api.baseten.co/v1", defaultModel: "llama-3-70b-instruct" },
    "RunPod Serverless":             { emoji: "🟣", color: "#8b5cf6", authType: "apikey", keyHint: "...", category: "fast", defaultUrl: "https://api.runpod.ai/v2/openai/v1", defaultModel: "meta-llama/Llama-3.3-70B-Instruct" },
    "Modal Labs":                    { emoji: "🟢", color: "#10b981", authType: "apikey", keyHint: "...", category: "cloud", defaultUrl: "https://api.modal.run/v1", defaultModel: "meta-llama-3.3-70b-instruct" },

    // Specialty & Gateways
    "Unify AI":                      { emoji: "🔄", color: "#6366f1", authType: "apikey", keyHint: "...", category: "router", defaultUrl: "https://api.unify.ai/v1", defaultModel: "llama-3.3-70b-instruct@groq" },
    "Martian AI":                    { emoji: "👽", color: "#ef4444", authType: "apikey", keyHint: "...", category: "router", defaultUrl: "https://api.withmartian.com/v1", defaultModel: "router" },
    "NotDiamond Router":             { emoji: "💎", color: "#38bdf8", authType: "apikey", keyHint: "...", category: "router", defaultUrl: "https://api.notdiamond.ai/v1", defaultModel: "notdiamond-auto" },
    "OpenPipe":                      { emoji: "🚰", color: "#f97316", authType: "apikey", keyHint: "...", category: "router", defaultUrl: "https://api.openpipe.ai/v1", defaultModel: "openpipe-default" },
    "Braintrust AI Proxy":           { emoji: "🧠", color: "#8b5cf6", authType: "apikey", keyHint: "...", category: "router", defaultUrl: "https://api.braintrust.dev/v1", defaultModel: "gpt-4o" },
    "Portkey AI Gateway":            { emoji: "🗝️", color: "#10b981", authType: "apikey", keyHint: "...", category: "router", defaultUrl: "https://api.portkey.ai/v1", defaultModel: "gpt-4o" },
    "Helicone AI Proxy":             { emoji: "🚁", color: "#3b82f6", authType: "apikey", keyHint: "...", category: "router", defaultUrl: "https://oai.h3loud.com/v1", defaultModel: "gpt-4o" },
    "LiteLLM Proxy":                 { emoji: "🔀", color: "#64748b", authType: "local", keyHint: "none needed", category: "router", defaultUrl: "http://localhost:4000/v1", defaultModel: "gpt-4o" },
    "AIPI Multiple Models Router":   { emoji: "⚡", color: "#38bdf8", authType: "local", keyHint: "none needed", category: "router", defaultUrl: "http://localhost:11434/v1", defaultModel: "auto/best-coding" },
    "Hermes Gateway":                { emoji: "🛡️", color: "#10b981", authType: "local", keyHint: "none needed", category: "router", defaultUrl: "http://localhost:11434/v1", defaultModel: "gpt-4o" },

    // Special Auth Providers
    "GitHub Copilot":                { emoji: "🐙", color: "#6e5494", authType: "github-copilot", keyHint: "Device OAuth", category: "cloud", defaultUrl: "https://api.githubcopilot.com", defaultModel: "gpt-4o" },
    "Claude Code":                   { emoji: "🤖", color: "#d97706", authType: "claude-import", keyHint: "Auto-Import", category: "cloud", defaultUrl: "https://api.anthropic.com", defaultModel: "claude-3-7-sonnet-20250219" },
    "Mistral Codestral":             { emoji: "👨‍💻", color: "#9333ea", authType: "apikey", keyHint: "...", category: "reasoning", defaultUrl: "https://codestral.mistral.ai/v1", defaultModel: "codestral-latest" },

    // Local Runtimes
    "Ollama (Local)":                { emoji: "🦙", color: "#22c55e", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:11434/v1", defaultModel: "llama3.3" },
    "LM Studio":                     { emoji: "🏠", color: "#0ea5e9", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:1234/v1", defaultModel: "local-model" },
    "Jan.ai (Local)":                { emoji: "🤖", color: "#2563eb", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:1337/v1", defaultModel: "tinyllama" },
    "LocalAI":                       { emoji: "🖥️", color: "#475569", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:8080/v1", defaultModel: "gpt-4" },
    "vLLM (Local)":                  { emoji: "🚀", color: "#16a34a", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:8000/v1", defaultModel: "meta-llama/Llama-3.3-70B-Instruct" },
    "llama.cpp Server":              { emoji: "🦙", color: "#ea580c", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:8080/v1", defaultModel: "ggml-model" },
    "KoboldCPP Engine":              { emoji: "🐉", color: "#b91c1c", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:5001/v1", defaultModel: "kobold-model" },
    "TabbyAPI ExLlamaV2":            { emoji: "🐱", color: "#f59e0b", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:5000/v1", defaultModel: "exl2-model" },
    "Text Generation Inference (TGI)":{ emoji: "🤗", color: "#eab308", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:8080/v1", defaultModel: "tgi-model" },
    "Aphrodite Engine":              { emoji: "🌺", color: "#ec4899", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:2242/v1", defaultModel: "aphrodite-model" },
    "SGLang Serving":                { emoji: "⚡", color: "#3b82f6", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:30000/v1", defaultModel: "sglang-model" },
    "Text Generation WebUI (Oobabooga)": { emoji: "🎭", color: "#8b5cf6", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:5000/v1", defaultModel: "textgen-model" },
    "GPT4All Desktop":               { emoji: "💻", color: "#06b6d4", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:4891/v1", defaultModel: "gpt4all-model" },
    "FastChat Controller":           { emoji: "💬", color: "#10b981", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:8000/v1", defaultModel: "vicuna-13b" },
    "TensorRT-LLM Triton Server":    { emoji: "🟢", color: "#76b900", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:8000/v1", defaultModel: "trt-llm-model" },
    "Mindie Server (Huawei Ascend)": { emoji: "🇨🇳", color: "#dc2626", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:1025/v1", defaultModel: "ascend-model" },
    "KServe ML Inference":           { emoji: "☸️", color: "#326ce5", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:8080/v1", defaultModel: "kserve-model" },
    "BentoML LLM Server":            { emoji: "🍱", color: "#f97316", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:3000/v1", defaultModel: "bentoml-model" },
    "Ray Serve LLM Cluster":         { emoji: "☀️", color: "#0284c7", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:8000/v1", defaultModel: "ray-serve-model" },
    "Triton Inference Server":       { emoji: "🔱", color: "#76b900", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:8000/v1", defaultModel: "triton-model" },
    "TorchServe Engine":             { emoji: "🔥", color: "#ee4c2c", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:8080/v1", defaultModel: "torchserve-model" },
    "MLflow Deployments Server":     { emoji: "📈", color: "#0194e2", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:5000/v1", defaultModel: "mlflow-model" },
    "Unsloth Inference Engine":      { emoji: "🦥", color: "#10b981", authType: "local", keyHint: "none needed", category: "local", defaultUrl: "http://localhost:8000/v1", defaultModel: "unsloth-model" },

    // Developer Applications & Web UIs
    "Dify AI Platform":              { emoji: "🧩", color: "#155eef", authType: "apikey", keyHint: "app-...", category: "apps", defaultUrl: "https://api.dify.ai/v1", defaultModel: "dify-app" },
    "Flowise AI":                    { emoji: "🌊", color: "#0ea5e9", authType: "local", keyHint: "none needed", category: "apps", defaultUrl: "http://localhost:3000/api/v1", defaultModel: "flowise-flow" },
    "Langflow Server":               { emoji: "🦜", color: "#10b981", authType: "local", keyHint: "none needed", category: "apps", defaultUrl: "http://localhost:7860/api/v1", defaultModel: "langflow-flow" },
    "AnythingLLM":                   { emoji: "📁", color: "#38bdf8", authType: "local", keyHint: "none needed", category: "apps", defaultUrl: "http://localhost:3001/api/v1", defaultModel: "anythingllm-workspace" },
    "Open WebUI":                    { emoji: "🌐", color: "#6366f1", authType: "local", keyHint: "none needed", category: "apps", defaultUrl: "http://localhost:3000/api/v1", defaultModel: "open-webui-model" },
    "LibreChat":                     { emoji: "💬", color: "#10b981", authType: "local", keyHint: "none needed", category: "apps", defaultUrl: "http://localhost:3080/api", defaultModel: "librechat-model" },
    "Lobe Chat":                     { emoji: "🤯", color: "#ec4899", authType: "local", keyHint: "none needed", category: "apps", defaultUrl: "http://localhost:3210/v1", defaultModel: "lobe-model" },
    "NextChat":                      { emoji: "⚡", color: "#06b6d4", authType: "local", keyHint: "none needed", category: "apps", defaultUrl: "http://localhost:3000/v1", defaultModel: "nextchat-model" },
    "SillyTavern Server":            { emoji: "🍺", color: "#f59e0b", authType: "local", keyHint: "none needed", category: "apps", defaultUrl: "http://localhost:8000/v1", defaultModel: "st-model" },
    "Faraday AI":                    { emoji: "🔒", color: "#64748b", authType: "local", keyHint: "none needed", category: "apps", defaultUrl: "http://localhost:11437/v1", defaultModel: "faraday-model" },

    // Enterprise & IDE Proxies
    "AWS Bedrock (Proxy)":           { emoji: "🟧", color: "#ff9900", authType: "local", keyHint: "none needed", category: "enterprise", defaultUrl: "http://localhost:8000/v1", defaultModel: "anthropic.claude-3-5-sonnet-20241022-v2:0" },
    "Azure OpenAI Service":          { emoji: "🟦", color: "#0078d4", authType: "apikey", keyHint: "...", category: "enterprise", defaultUrl: "https://YOUR_RESOURCE.openai.azure.com/openai/deployments/YOUR_DEPLOYMENT", defaultModel: "gpt-4o" },
    "Google Vertex AI (Express Proxy)":{ emoji: "🌈", color: "#4285f4", authType: "local", keyHint: "none needed", category: "enterprise", defaultUrl: "http://localhost:8080/v1", defaultModel: "gemini-2.0-flash" },
    "Databricks Model Serving":      { emoji: "🧱", color: "#ff3621", authType: "apikey", keyHint: "dapi...", category: "enterprise", defaultUrl: "https://YOUR_DATABRICKS.cloud.databricks.com/serving-endpoints", defaultModel: "databricks-dbrx-instruct" },
    "Snowflake Cortex AI":           { emoji: "❄️", color: "#29b5e8", authType: "apikey", keyHint: "...", category: "enterprise", defaultUrl: "https://YOUR_ACCOUNT.snowflakecomputing.com/api/v2/cortex/inference", defaultModel: "snowflake-arctic" },
    "Oracle Cloud Infrastructure AI":{ emoji: "🔴", color: "#f80000", authType: "apikey", keyHint: "...", category: "enterprise", defaultUrl: "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/v1", defaultModel: "cohere.command-r-plus" },
    "IBM watsonx.ai":                { emoji: "🟦", color: "#054ada", authType: "apikey", keyHint: "...", category: "enterprise", defaultUrl: "https://us-south.ml.cloud.ibm.com/v1", defaultModel: "ibm/granite-3-8b-instruct" },
    "SAP Generative AI Hub":         { emoji: "🏢", color: "#008fd3", authType: "apikey", keyHint: "...", category: "enterprise", defaultUrl: "https://api.ai.prod.eu-central-1.aws.ml.hana.ondemand.com/v2", defaultModel: "gpt-4o" },
    "Cursor IDE Local Proxy":        { emoji: "🖱️", color: "#38bdf8", authType: "local", keyHint: "none needed", category: "apps", defaultUrl: "http://localhost:11434/v1", defaultModel: "cursor-small" },
    "Claude Code CLI Gateway":       { emoji: "🤖", color: "#d97706", authType: "anthropic", keyHint: "...", category: "apps", defaultUrl: "http://localhost:11434/v1", defaultModel: "claude-3-7-sonnet-20250219" },
    "AIPI Antigravity Cloud Router": { emoji: "⚡", color: "#8b5cf6", authType: "local", keyHint: "none needed", category: "router", defaultUrl: "https://cloudcode-pa.googleapis.com", defaultModel: "antigravity/claude-sonnet-4-6" },
    "OpenCode CLI Gateway":          { emoji: "💻", color: "#6366f1", authType: "local", keyHint: "none needed", category: "apps", defaultUrl: "http://localhost:11434/v1", defaultModel: "hy3-free" },
    "OpenCode Zen Gateway":          { emoji: "⚡", color: "#06b6d4", authType: "apikey", keyHint: "sk-...", category: "cloud", defaultUrl: "https://opencode.ai/zen/v1", defaultModel: "hy3-free" },
    "Continue.dev Local Proxy":      { emoji: "⏩", color: "#10b981", authType: "local", keyHint: "none needed", category: "apps", defaultUrl: "http://localhost:65433/v1", defaultModel: "continue-model" },
    "Aider CLI Local Proxy":         { emoji: "🛠️", color: "#f59e0b", authType: "local", keyHint: "none needed", category: "apps", defaultUrl: "http://localhost:8000/v1", defaultModel: "aider-model" },
};

var HUB_SPECIAL_PROVIDERS = [
    { name: "GitHub Copilot", base_url: "https://api.githubcopilot.com", format: "openai",
      default_model: "gpt-4o", notes: "GitHub Copilot API via Device OAuth" },
    { name: "Claude Code",    base_url: "https://api.anthropic.com", format: "anthropic",
      default_model: "claude-3-7-sonnet-20250219", notes: "Auto-import from Claude Code CLI session" },
    { name: "Ollama (Local)", base_url: "http://localhost:11434/v1", format: "openai",
      default_model: "llama3.3", notes: "Local Ollama server — no key needed" },
    { name: "LM Studio",      base_url: "http://localhost:1234/v1", format: "openai",
      default_model: "local-model", notes: "Local LM Studio server — no key needed" },
];

var hubModalProvider = null;
var hubPollInterval  = null;
var _lastProviderStatuses = [];
var _currentHubCategory = "all";
var _currentHubSearch = "";

(function injectHubStyles() {
    if (document.getElementById("hub-styles")) return;
    const s = document.createElement("style");
    s.id = "hub-styles";
    s.textContent = `
    .hub-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;
    }
    .hub-card:hover {
        border-color: #38bdf8;
        box-shadow: 0 6px 24px rgba(0,0,0,0.4);
    }
    .hub-preset-card {
        background: #1e293b;
        border: 1px solid #2d3f55;
        border-radius: 10px;
        padding: 14px;
        cursor: pointer;
        transition: border-color 0.25s, transform 0.12s, box-shadow 0.2s, background 0.15s;
        user-select: none;
    }
    .hub-preset-card:hover {
        border-color: #38bdf8;
        background: #182338;
        transform: translateY(-2px);
        box-shadow: 0 8px 28px rgba(0,0,0,0.45);
    }
    .hub-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    @keyframes hubPulse { 0%,100%{opacity:1} 50%{opacity:0.35} }
    .hub-dot-pulsing { animation: hubPulse 1.2s ease-in-out infinite; }
    .hub-cat-btn {
        background: #0f172a;
        border: 1px solid #334155;
        color: #94a3b8;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.15s ease;
        white-space: nowrap;
    }
    .hub-cat-btn:hover {
        background: #1e293b;
        color: #f8fafc;
        border-color: #475569;
    }
    .hub-cat-btn.active {
        background: #6366f1;
        color: #fff;
        border-color: #6366f1;
        box-shadow: 0 2px 10px rgba(99,102,241,0.4);
    }
    `;
    document.head.appendChild(s);
})();

function getAllUniquePresets() {
    const map = new Map();
    HUB_SPECIAL_PROVIDERS.forEach(p => map.set(p.name, p));
    if (Array.isArray(window.PROVIDER_PRESETS)) {
        window.PROVIDER_PRESETS.forEach(p => {
            if (!map.has(p.name)) {
                map.set(p.name, p);
            }
        });
    }
    return Array.from(map.values());
}

function initProviderHub() {
    renderHubControls();
    renderHubPresetGrid();
    loadProviderHubStatus();
}

function renderHubControls() {
    const filterContainer = document.getElementById("hub-filter-controls");
    if (!filterContainer) return;

    const categories = [
        { id: "all", label: "🌟 All (169+)" },
        { id: "popular", label: "🔥 Popular" },
        { id: "cloud", label: "☁️ Cloud Giants" },
        { id: "reasoning", label: "🧠 Reasoning & Code" },
        { id: "fast", label: "⚡ Ultra-Fast" },
        { id: "asian", label: "🌏 Asian Leaders" },
        { id: "local", label: "💻 Local / Offline" },
        { id: "router", label: "🌐 Routers" },
        { id: "apps", label: "🤖 Agent Web UIs" },
        { id: "enterprise", label: "🛡️ Enterprise" }
    ];

    filterContainer.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 14px;">
            <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
                ${categories.map(c => `
                    <button class="hub-cat-btn ${c.id === _currentHubCategory ? 'active' : ''}" onclick="setHubCategory('${c.id}')">${c.label}</button>
                `).join('')}
            </div>
            <div style="position: relative; min-width: 240px; flex: 1; max-width: 360px;">
                <input type="text" id="hub-search-input" class="form-control" placeholder="🔍 Search providers or models..." value="${escapeHtml(_currentHubSearch)}" style="padding-left: 12px; font-size: 13px;">
            </div>
        </div>
    `;

    const searchInput = document.getElementById("hub-search-input");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            _currentHubSearch = e.target.value.trim().toLowerCase();
            renderHubPresetGrid();
        });
    }
}

function setHubCategory(catId) {
    _currentHubCategory = catId;
    renderHubControls();
    renderHubPresetGrid();
}

async function loadProviderHubStatus() {
    const bar = document.getElementById("hub-status-bar-text");
    if (bar) bar.textContent = "Scanning provider connections…";
    const grid = document.getElementById("hub-providers-grid");
    if (grid) grid.innerHTML = `<div style="grid-column:1/-1;color:#64748b;font-size:13px;padding:12px 0;display:flex;align-items:center;gap:10px;"><span class="hub-dot hub-dot-pulsing" style="background:#38bdf8;"></span> Pinging providers…</div>`;

    try {
        const r = await fetch("/v1/providers/status-all");
        const statuses = await r.json();
        _lastProviderStatuses = Array.isArray(statuses) ? statuses : [];
        if (!grid) return;
        if (!statuses || !statuses.length) {
            grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:28px 0;color:#64748b;font-size:14px;"><div style="font-size:32px;margin-bottom:8px;">🔌</div>No providers connected yet — click any preset card below to connect one.</div>`;
            if (bar) bar.textContent = "No providers saved";
            return;
        }

        grid.innerHTML = statuses.map((s, idx) => {
            const meta = HUB_PROVIDER_META[s.name] || { emoji: "⚙️", color: "#64748b" };
            const isConnected = (s.status === "connected" || (s.ok && s.status !== "unauthorized"));
            const isUnauthorized = (s.status === "unauthorized");

            let dotClr = "#ef4444";
            let dotCls = "hub-dot-pulsing";
            let latBadge = "";
            let statusText = "";

            if (isConnected) {
                dotClr = "#22c55e";
                dotCls = "";
                latBadge = `<span style="background:rgba(34,197,94,0.12);color:#22c55e;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600;">${s.latency_ms || 0}ms</span>`;
                statusText = `<div style="color:#64748b;font-size:11px;margin-top:3px;cursor:pointer;" title="Click to view models" onclick="showProviderModelsModal('${escapeHtml(s.name)}')"><strong style="color:#38bdf8;">${s.model_count || 0} models</strong> available 🔍</div>`;
            } else if (isUnauthorized) {
                dotClr = "#f59e0b";
                dotCls = "hub-dot-pulsing";
                latBadge = `<span style="background:rgba(245,158,11,0.15);color:#f59e0b;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600;">Unauthorized</span>`;
                statusText = `<div style="color:#fbbf24;font-size:11px;margin-top:3px;font-weight:500;">⚠️ Invalid / Expired API Key</div>`;
            } else {
                dotClr = "#ef4444";
                dotCls = "hub-dot-pulsing";
                latBadge = `<span style="background:rgba(239,68,68,0.12);color:#ef4444;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600;">Offline</span>`;
                statusText = `<div style="color:#f87171;font-size:11px;margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${s.error || "Unreachable"}">${s.error || "Connection failed"}</div>`;
            }

            const defaultM = (s.sample_models && s.sample_models[0]) || "";

            return `<div class="hub-card" id="hub-card-${idx}" style="border-color:${meta.color}40;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:26px;line-height:1;">${meta.emoji}</span>
                        <div>
                            <div style="font-weight:600;color:#f1f5f9;font-size:14px;display:flex;align-items:center;gap:6px;">
                                ${escapeHtml(s.name)}
                            </div>
                            ${statusText}
                        </div>
                    </div>
                    <div style="display:flex;align-items:center;gap:8px;flex-shrink:0;margin-left:8px;">
                        <span class="hub-dot ${dotCls}" style="background:${dotClr};"></span>
                        ${latBadge}
                    </div>
                </div>
                <div style="display:flex;gap:6px;margin-top:14px;flex-wrap:wrap;">
                    <button class="btn btn-outline btn-sm" onclick="testHubProviderDirectly('${escapeHtml(s.name)}')" title="Test Live Connection" style="font-size:11px;padding:4px 8px;">⚡ Test</button>
                    <button class="btn btn-outline btn-sm" onclick="openConnectModal('${escapeHtml(s.name)}')" title="Reconfigure" style="font-size:11px;padding:4px 8px;flex:1;">✏️ Edit</button>
                    <button class="btn btn-primary btn-sm" onclick="openInPlayground('${escapeHtml(s.name)}', '${escapeHtml(defaultM)}')" title="Open in Playground" style="font-size:11px;padding:4px 8px;">🚀 Play</button>
                    <button class="btn-hub-delete" onclick="quickDeleteProvider('${escapeHtml(s.name)}')" title="Delete Provider" style="color:#ef4444;border:1px solid rgba(239,68,68,0.4);background:transparent;border-radius:6px;padding:4px 8px;cursor:pointer;font-size:11px;transition:background 0.15s;" onmouseover="this.style.background='rgba(239,68,68,0.1)'" onmouseout="this.style.background='transparent'">✕</button>
                </div>
            </div>`;
        }).join("");

        const okCount = statuses.filter(s => s.status === "connected" || (s.ok && s.status !== "unauthorized")).length;
        if (bar) bar.textContent = `${okCount} / ${statuses.length} providers online`;
    } catch (e) {
        if (grid) grid.innerHTML = `<div style="grid-column:1/-1;color:#f87171;font-size:13px;padding:12px 0;">⚠️ Could not reach gateway: ${e.message}</div>`;
        if (bar) bar.textContent = "Gateway unreachable";
    }
}

async function testHubProviderDirectly(providerName) {
    const bar = document.getElementById("hub-status-bar-text");
    if (bar) bar.textContent = `Testing ${providerName}…`;
    try {
        const confRes = await fetch("/v1/config");
        const conf = await confRes.json();
        const prov = (conf.providers || []).find(p => p.name === providerName);
        if (!prov) { alert("Provider configuration not found."); return; }

        const r = await fetch("/v1/providers/test-connection", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                provider_name: prov.name,
                api_key: prov.api_key || "ollama",
                base_url: prov.base_url,
                format: prov.format || "openai"
            })
        });
        const d = await r.json();
        const errMsg = (d.error && typeof d.error === 'object') ? (d.error.message || JSON.stringify(d.error)) : (d.error || d.message || "Unreachable");
        if (d.connected) {
            alert(`✅ ${providerName} is ONLINE!\n\nLatency: ${d.latency_ms}ms\nModels Found: ${d.models_count}\n` + (d.sample_models ? `Sample Models: ${d.sample_models.slice(0, 5).join(", ")}` : ""));
        } else {
            alert(`❌ ${providerName} connection failed:\n\n${errMsg}`);
        }
        loadProviderHubStatus();
    } catch (e) {
        alert("Error testing provider: " + e.message);
    }
}

function showProviderModelsModal(providerName) {
    const status = _lastProviderStatuses.find(s => s.name === providerName);
    if (!status || !status.sample_models || !status.sample_models.length) {
        openConnectModal(providerName);
        return;
    }
    const modelListStr = status.sample_models.map(m => `• ${m}`).join("\n");
    if (confirm(`Models available for ${providerName} (${status.model_count} total):\n\n${modelListStr}\n\nWould you like to test these models in the Playground?`)) {
        openInPlayground(providerName, status.sample_models[0]);
    }
}

function openInPlayground(providerName, modelId) {
    // Switch to Playground tab
    const navItem = document.querySelector('.nav-item[data-tab="playground"]');
    if (navItem) navItem.click();

    setTimeout(() => {
        const provSel = document.getElementById("play-provider");
        if (provSel && providerName) {
            for (let i = 0; i < provSel.options.length; i++) {
                if (provSel.options[i].value === providerName) {
                    provSel.selectedIndex = i;
                    break;
                }
            }
        }
        const modelInp = document.getElementById("play-model");
        if (modelInp && modelId) {
            modelInp.value = modelId;
        }
        const promptInp = document.getElementById("play-prompt");
        if (promptInp) promptInp.focus();
    }, 100);
}

function renderHubPresetGrid() {
    const grid = document.getElementById("hub-preset-grid");
    if (!grid) return;
    const allPresets = getAllUniquePresets();

    // Filter by category and search
    const filtered = allPresets.filter(p => {
        const meta = HUB_PROVIDER_META[p.name] || { category: p.category || "cloud" };
        const cat = meta.category || p.category || "cloud";

        if (_currentHubCategory === "popular") {
            const popularNames = ["OpenAI", "Anthropic", "Google Gemini (OpenAI Compat)", "DeepSeek AI", "Groq Cloud", "Mistral AI", "xAI (Grok)", "OpenRouter", "Ollama (Local)", "GitHub Copilot", "Claude Code", "Moonshot AI (Kimi)", "Alibaba DashScope (Qwen)"];
            if (!popularNames.includes(p.name)) return false;
        } else if (_currentHubCategory !== "all" && cat !== _currentHubCategory) {
            return false;
        }

        if (_currentHubSearch) {
            const str = `${p.name} ${p.default_model || ''} ${p.notes || ''} ${p.base_url || ''}`.toLowerCase();
            if (!str.includes(_currentHubSearch)) return false;
        }

        return true;
    });

    if (filtered.length === 0) {
        grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:32px 0;color:#64748b;font-size:14px;">No provider presets match "<em>${escapeHtml(_currentHubSearch)}</em>".</div>`;
        return;
    }

    grid.innerHTML = filtered.map(p => {
        const meta = HUB_PROVIDER_META[p.name] || { emoji: "⚙️", color: "#64748b", authType: "apikey" };
        const badge = getBadgeForAuthType(meta.authType);
        return `<div class="hub-preset-card" data-provider-name="${escapeHtml(p.name)}" title="Click to connect ${escapeHtml(p.name)}">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div style="display:flex;align-items:center;gap:10px;overflow:hidden;">
                    <span style="font-size:22px;line-height:1;flex-shrink:0;">${meta.emoji}</span>
                    <div style="overflow:hidden;">
                        <div style="font-weight:600;color:#f1f5f9;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(p.name)}</div>
                        <div style="color:#64748b;font-size:11px;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(p.default_model || p.notes || "")}</div>
                    </div>
                </div>
                ${badge}
            </div>
        </div>`;
    }).join("");

    // Safely attach event listeners to all preset cards
    grid.querySelectorAll(".hub-preset-card").forEach(card => {
        card.addEventListener("click", () => {
            const providerName = card.getAttribute("data-provider-name");
            if (providerName) openConnectModal(providerName);
        });
    });
}

function getBadgeForAuthType(t) {
    const map = {
        apikey:          `<span style="background:rgba(99,102,241,0.15);color:#818cf8;padding:2px 8px;border-radius:20px;font-size:10px;white-space:nowrap;flex-shrink:0;">API Key</span>`,
        "github-copilot":`<span style="background:rgba(110,84,148,0.2);color:#a78bfa;padding:2px 8px;border-radius:20px;font-size:10px;white-space:nowrap;flex-shrink:0;">Device OAuth</span>`,
        "claude-import": `<span style="background:rgba(217,119,6,0.15);color:#fbbf24;padding:2px 8px;border-radius:20px;font-size:10px;white-space:nowrap;flex-shrink:0;">Auto-Import</span>`,
        "oauth-antigravity":`<span style="background:rgba(56,189,248,0.15);color:#38bdf8;padding:2px 8px;border-radius:20px;font-size:10px;white-space:nowrap;flex-shrink:0;">🚀 Antigravity OAuth</span>`,
        oauth:           `<span style="background:rgba(66,133,244,0.15);color:#60a5fa;padding:2px 8px;border-radius:20px;font-size:10px;white-space:nowrap;flex-shrink:0;">OAuth</span>`,
        local:           `<span style="background:rgba(34,197,94,0.12);color:#4ade80;padding:2px 8px;border-radius:20px;font-size:10px;white-space:nowrap;flex-shrink:0;">Local</span>`,
    };
    return map[t] || map.apikey;
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

async function openConnectModal(providerName) {
    const allPresets = getAllUniquePresets();
    let preset = allPresets.find(p => p.name === providerName) || { name: providerName };
    const meta = HUB_PROVIDER_META[providerName] || { emoji: "⚙️", authType: "apikey", keyHint: "...", defaultUrl: "", defaultModel: "" };

    // Check if provider is currently configured in config.json / active list
    let existingConfig = null;
    try {
        const confRes = await fetch("/v1/config");
        if (confRes.ok) {
            const conf = await confRes.json();
            if (conf.providers) {
                existingConfig = conf.providers.find(p => p.name === providerName);
            }
        }
    } catch (_) {}

    const baseUrl = (existingConfig && existingConfig.base_url) || preset.base_url || meta.defaultUrl || "";
    const defaultModel = (existingConfig && existingConfig.default_model) || preset.default_model || meta.defaultModel || "";
    const format = (existingConfig && existingConfig.format) || preset.format || "openai";

    hubModalProvider = { ...preset, ...meta, base_url: baseUrl, default_model: defaultModel, format: format };

    document.getElementById("hub-modal-logo").textContent = meta.emoji;
    document.getElementById("hub-modal-title").textContent = existingConfig ? `Reconfigure ${providerName}` : `Connect ${providerName}`;
    document.getElementById("hub-modal-subtitle").textContent = baseUrl ? `Base: ${baseUrl}` : "Universal AI Provider Gateway";

    ["hub-device-flow","hub-apikey-form","hub-oauth-flow","hub-claude-import"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = "none";
    });
    const tr = document.getElementById("hub-test-result");
    if (tr) { tr.style.display = "none"; tr.textContent = ""; }

    const baseUrlInp = document.getElementById("hub-base-url-input");
    if (baseUrlInp) baseUrlInp.value = baseUrl;

    const modelInp = document.getElementById("hub-model-input");
    if (modelInp) modelInp.value = defaultModel;

    if (meta.authType === "github-copilot") {
        document.getElementById("hub-device-flow").style.display = "block";
        startGitHubCopilotFlow();
    } else if (meta.authType === "claude-import") {
        document.getElementById("hub-claude-import").style.display = "block";
    } else if (meta.authType === "oauth-antigravity") {
        document.getElementById("hub-oauth-flow").style.display = "block";
        document.getElementById("hub-oauth-desc").textContent = `Connect your Google account with Antigravity OAuth to access Claude Sonnet 4.6, Claude Opus 4.6 Thinking, and Gemini 2.5/3.5 Flash models directly in AIPI with native Multiple Models Router.`;
        const btnLbl = document.getElementById("hub-oauth-btn-label");
        if (btnLbl) btnLbl.textContent = "🚀 Authorize with Google Antigravity";
    } else if (meta.authType === "oauth") {
        document.getElementById("hub-oauth-flow").style.display = "block";
        document.getElementById("hub-oauth-desc").textContent = `Connect your Google account to access Gemini models through AIPI.`;
        const btnLbl = document.getElementById("hub-oauth-btn-label");
        if (btnLbl) btnLbl.textContent = "🔗 Open Google Authorization Page";
    } else if (meta.authType === "local") {
        document.getElementById("hub-apikey-form").style.display = "block";
        const inp = document.getElementById("hub-api-key-input");
        if (inp) {
            inp.type = "text";
            inp.value = "ollama";
            inp.placeholder = 'No key needed — use "ollama" or leave blank';
        }
    } else {
        document.getElementById("hub-apikey-form").style.display = "block";
        const inp = document.getElementById("hub-api-key-input");
        if (inp) {
            inp.type = "password";
            inp.value = "";
            inp.placeholder = existingConfig ? `Leave blank to keep existing key, or paste new key (${meta.keyHint || "..."})` : `Paste your ${providerName} API key (${meta.keyHint || "..."})`;
            setTimeout(() => inp.focus(), 150);
        }
    }

    const modal = document.getElementById("provider-connect-modal");
    if (modal) modal.style.display = "flex";
}

function closeConnectModal() {
    const modal = document.getElementById("provider-connect-modal");
    if (modal) modal.style.display = "none";
    if (hubPollInterval) { clearInterval(hubPollInterval); hubPollInterval = null; }
}

function toggleHubKeyVisibility() {
    const inp = document.getElementById("hub-api-key-input");
    const btn = document.getElementById("hub-eye-btn");
    if (!inp) return;
    inp.type = inp.type === "password" ? "text" : "password";
    if (btn) btn.textContent = inp.type === "text" ? "🙈" : "👁";
}

async function startGitHubCopilotFlow() {
    const st = document.getElementById("hub-status-text");
    if (st) st.textContent = "Requesting device code from GitHub…";
    try {
        const r = await fetch("/v1/oauth/github-copilot/start", { method:"POST", headers:{"Content-Type":"application/json"}, body:"{}" });
        const d = await r.json();
        if (!d.user_code) { if (st) st.textContent = "Error: " + (d.error || "No device code"); return; }
        const ce = document.getElementById("hub-user-code");
        const le = document.getElementById("hub-verify-link");
        if (ce) ce.textContent = d.user_code;
        if (le) { le.textContent = d.verification_uri || "https://github.com/login/device"; le.href = le.textContent; }
        window.open(d.verification_uri || "https://github.com/login/device", "_blank");
        if (st) st.textContent = "Waiting for you to authorize on GitHub…";
        let polls = 0;
        hubPollInterval = setInterval(async () => {
            polls++;
            if (polls > 36) { clearInterval(hubPollInterval); if (st) st.textContent = "⏱ Timed out. Try again."; return; }
            try {
                const pr = await fetch("/v1/oauth/github-copilot/poll", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({ device_code: d.device_code }) });
                const pd = await pr.json();
                if (pd.access_token) {
                    clearInterval(hubPollInterval);
                    if (st) st.textContent = "✅ Authorized! Saving…";
                    await fetch("/v1/providers/connect-key", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({ provider_name:"GitHub Copilot", api_key: pd.access_token, base_url:"https://api.githubcopilot.com", format:"openai", default_model:"gpt-4o", notes:"Device OAuth" }) });
                    setTimeout(() => { closeConnectModal(); loadProviderHubStatus(); }, 1000);
                } else if (pd.error && pd.error !== "authorization_pending" && pd.error !== "slow_down") {
                    clearInterval(hubPollInterval);
                    if (st) st.textContent = "❌ " + pd.error;
                }
            } catch (_) {}
        }, (d.interval || 5) * 1000);
    } catch (e) { if (st) st.textContent = "❌ " + e.message; }
}

function startOAuthRedirect() {
    const btn = document.getElementById("hub-btn-oauth-start");
    const lbl = document.getElementById("hub-oauth-btn-label");
    if (btn) btn.disabled = true;
    if (lbl) lbl.textContent = "🌐 Opening browser…";
    const port = window.AIPI_PORT || 11434;
    if (hubModalProvider && (hubModalProvider.authType === "oauth-antigravity" || (hubModalProvider.name && hubModalProvider.name.includes("Antigravity")))) {
        window.open(`http://127.0.0.1:${port}/v1/oauth/antigravity/start`, "_blank");
    } else {
        window.open(`http://127.0.0.1:${port}/v1/oauth/google/start`, "_blank");
    }
    setTimeout(() => {
        if (btn) btn.disabled = false;
        if (lbl) lbl.textContent = (hubModalProvider && hubModalProvider.authType === "oauth-antigravity") ? "🚀 Authorize with Google Antigravity" : "🔗 Open Authorization Page";
    }, 3000);
}

async function runClaudeImport() {
    const result = document.getElementById("hub-import-result");
    if (!result) return;
    result.style.display = "block";
    result.style.cssText += ";background:#0f172a;border:1px solid #334155;color:#94a3b8;";
    result.textContent = "🔍 Scanning for Claude Code credentials…";
    try {
        const r = await fetch("/v1/oauth/claude-code/import", { method:"POST", headers:{"Content-Type":"application/json"}, body:"{}" });
        const d = await r.json();
        if (d.ok) {
            result.style.cssText += ";background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);color:#4ade80;";
            result.innerHTML = `✅ <strong>${d.message || "Imported!"}</strong>`;
            setTimeout(() => { closeConnectModal(); loadProviderHubStatus(); }, 1500);
        } else {
            result.style.cssText += ";background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#f87171;";
            result.textContent = "❌ " + (d.error || "No credentials found.");
        }
    } catch (e) { result.style.color = "#f87171"; result.textContent = "❌ " + e.message; }
}

async function testHubConnection() {
    if (!hubModalProvider) return;
    const key = (document.getElementById("hub-api-key-input")?.value || "").trim();
    const baseUrl = (document.getElementById("hub-base-url-input")?.value || hubModalProvider.base_url || "").trim();
    const result = document.getElementById("hub-test-result");
    const btn = document.getElementById("hub-btn-test");

    if (!key && hubModalProvider.authType !== "local") {
        showHubResult(result, false, "Please enter an API key first.");
        return;
    }
    if (!baseUrl) {
        showHubResult(result, false, "Please enter a Base URL.");
        return;
    }

    if (btn) { btn.disabled = true; btn.textContent = "⚡ Testing…"; }
    showHubResult(result, null, "Testing connection…");

    try {
        const r = await fetch("/v1/providers/test-connection", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                provider_name: hubModalProvider.name,
                api_key: key || "ollama",
                base_url: baseUrl,
                format: hubModalProvider.format || "openai"
            })
        });
        const d = await r.json();
        const errMsg = (d.error && typeof d.error === 'object') ? (d.error.message || JSON.stringify(d.error)) : (d.message || d.error || "Connection failed. Check API key or URL.");
        if (d.connected) {
            showHubResult(result, true, `✅ Connected! ${d.models_count} models found in ${d.latency_ms}ms` + (d.sample_models?.length ? `\nSample: ${d.sample_models.slice(0, 4).join(", ")}` : ""));
        } else {
            showHubResult(result, false, "❌ " + errMsg);
        }
    } catch (e) {
        showHubResult(result, false, "❌ Network error: " + e.message);
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = "⚡ Test Connection"; }
    }
}

function showHubResult(el, ok, msg) {
    if (!el) return;
    el.style.display = "block";
    el.style.whiteSpace = "pre-line";
    if (ok === null) {
        el.style.background = "#0f172a";
        el.style.border = "1px solid #334155";
        el.style.color = "#94a3b8";
    } else if (ok) {
        el.style.background = "rgba(34,197,94,0.1)";
        el.style.border = "1px solid rgba(34,197,94,0.3)";
        el.style.color = "#4ade80";
    } else {
        el.style.background = "rgba(239,68,68,0.1)";
        el.style.border = "1px solid rgba(239,68,68,0.3)";
        el.style.color = "#f87171";
    }
    el.textContent = msg;
}

async function saveHubConnection() {
    if (!hubModalProvider) return;
    const key = (document.getElementById("hub-api-key-input")?.value || "").trim();
    const baseUrl = (document.getElementById("hub-base-url-input")?.value || hubModalProvider.base_url || "").trim();
    const defaultModel = (document.getElementById("hub-model-input")?.value || hubModalProvider.default_model || "").trim();
    const result = document.getElementById("hub-test-result");
    const btn = document.getElementById("hub-btn-save");

    if (!key && hubModalProvider.authType !== "local") {
        showHubResult(result, false, "❌ Please enter an API key.");
        return;
    }
    if (!baseUrl) {
        showHubResult(result, false, "❌ Please enter a Base URL.");
        return;
    }

    if (btn) { btn.disabled = true; btn.textContent = "⏳ Saving…"; }

    try {
        const r = await fetch("/v1/providers/connect-key", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                provider_name: hubModalProvider.name,
                api_key: key || "ollama",
                base_url: baseUrl,
                default_model: defaultModel,
                format: hubModalProvider.format || "openai"
            })
        });
        const d = await r.json();
        if (d.status === "ok") {
            showHubResult(result, true, d.message || "Saved successfully!");
            setTimeout(() => {
                closeConnectModal();
                loadProviderHubStatus();
                if (typeof window.loadDashboardData === "function") window.loadDashboardData();
                if (typeof window.loadMgmtProviders === "function") window.loadMgmtProviders();
                if (typeof window.loadModelList === "function") window.loadModelList();
            }, 800);
        } else {
            showHubResult(result, false, "❌ " + (d.error || "Failed to save provider."));
        }
    } catch (e) {
        showHubResult(result, false, "❌ " + e.message);
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = "✅ Connect & Save"; }
    }
}

async function quickDeleteProvider(name) {
    if (!confirm(`Remove "${name}" from AIPI?`)) return;
    try {
        await fetch("/v1/providers/delete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name })
        });
        loadProviderHubStatus();
        if (typeof window.loadDashboardData === "function") window.loadDashboardData();
        if (typeof window.loadMgmtProviders === "function") window.loadMgmtProviders();
        if (typeof window.loadModelList === "function") window.loadModelList();
    } catch (e) {
        alert("Error: " + e.message);
    }
}

window.quickDeleteProvider = quickDeleteProvider;
window.openConnectModal = openConnectModal;
window.closeConnectModal = closeConnectModal;
window.loadProviderHubStatus = loadProviderHubStatus;
window.initProviderHub = initProviderHub;
window.saveHubConnection = saveHubConnection;
window.testHubConnection = testHubConnection;
window.toggleHubKeyVisibility = toggleHubKeyVisibility;
window.setHubCategory = setHubCategory;
window.testHubProviderDirectly = testHubProviderDirectly;
window.showProviderModelsModal = showProviderModelsModal;
window.openInPlayground = openInPlayground;

document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("provider-connect-modal");
    if (modal) {
        modal.addEventListener("click", function(e) {
            if (e.target === this) closeConnectModal();
        });
    }

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeConnectModal();
        }
    });

    const keyInput = document.getElementById("hub-api-key-input");
    if (keyInput) {
        keyInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") saveHubConnection();
        });
    }

    document.querySelectorAll(".nav-item[data-tab]").forEach(btn => {
        btn.addEventListener("click", () => {
            if (btn.dataset.tab === "provider-hub") {
                setTimeout(initProviderHub, 50);
            }
        });
    });

    setTimeout(initProviderHub, 100);
});
