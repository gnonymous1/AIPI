/**
 * AIPI - Complete 169+ AI Provider Presets Library
 * Synchronized with providers_preset.py
 */
window.PROVIDER_PRESETS = [
  // ── Top Primary Labs & Cloud Giants (1-20) ──────────────────────────
  {
    "name": "OpenAI",
    "category": "cloud",
    "base_url": "https://api.openai.com/v1",
    "format": "openai",
    "default_model": "gpt-4o",
    "notes": "Official OpenAI API (GPT-4o, o1, o3-mini)"
  },
  {
    "name": "Google Antigravity",
    "category": "cloud",
    "base_url": "https://cloudcode-pa.googleapis.com",
    "format": "antigravity",
    "default_model": "antigravity/gemini-3.7-flash-high",
    "notes": "Google Antigravity Consumer OAuth (Gemini 3.7 Flash, Claude Sonnet 4.6, GPT-OSS 120B)"
  },
  {
    "name": "Anthropic",
    "category": "cloud",
    "base_url": "https://api.anthropic.com/v1",
    "format": "anthropic",
    "default_model": "claude-3-7-sonnet-20250219",
    "notes": "Official Anthropic Claude API (Sonnet 3.7 & Haiku)"
  },
  {
    "name": "Google Gemini (OpenAI Compat)",
    "category": "cloud",
    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
    "format": "openai",
    "default_model": "gemini-2.0-flash",
    "notes": "Google GenAI OpenAI-compatible endpoint"
  },
  {
    "name": "DeepSeek AI",
    "category": "reasoning",
    "base_url": "https://api.deepseek.com",
    "format": "openai",
    "default_model": "deepseek-chat",
    "notes": "DeepSeek V3 & R1 official reasoning API"
  },
  {
    "name": "Groq Cloud",
    "category": "fast",
    "base_url": "https://api.groq.com/openai/v1",
    "format": "openai",
    "default_model": "llama-3.3-70b-versatile",
    "notes": "Ultra-fast LPU inference engine by Groq"
  },
  {
    "name": "Mistral AI",
    "category": "cloud",
    "base_url": "https://api.mistral.ai/v1",
    "format": "openai",
    "default_model": "mistral-large-latest",
    "notes": "Official Mistral AI API & Codestral"
  },
  {
    "name": "xAI (Grok)",
    "category": "cloud",
    "base_url": "https://api.x.ai/v1",
    "format": "openai",
    "default_model": "grok-2-latest",
    "notes": "xAI Grok-2 & Grok-3 official API"
  },
  {
    "name": "Cohere",
    "category": "cloud",
    "base_url": "https://api.cohere.com/v2",
    "format": "openai",
    "default_model": "command-r-plus",
    "notes": "Cohere Command R+ & Embed API"
  },
  {
    "name": "Perplexity AI",
    "category": "cloud",
    "base_url": "https://api.perplexity.ai",
    "format": "openai",
    "default_model": "sonar-pro",
    "notes": "Perplexity online web search models"
  },
  {
    "name": "Cerebras Cloud",
    "category": "fast",
    "base_url": "https://api.cerebras.ai/v1",
    "format": "openai",
    "default_model": "llama3.3-70b",
    "notes": "Cerebras Wafer-Scale Engine (2000+ tok/s)"
  },
  {
    "name": "SambaNova Cloud",
    "category": "fast",
    "base_url": "https://api.sambanova.ai/v1",
    "format": "openai",
    "default_model": "Meta-Llama-3.3-70B-Instruct",
    "notes": "SambaNova Reconfigurable Dataflow Unit"
  },
  {
    "name": "Together AI",
    "category": "fast",
    "base_url": "https://api.together.xyz/v1",
    "format": "openai",
    "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "notes": "Together AI fast open-source inference"
  },
  {
    "name": "Fireworks AI",
    "category": "fast",
    "base_url": "https://api.fireworks.ai/inference/v1",
    "format": "openai",
    "default_model": "accounts/fireworks/models/llama-v3p3-70b-instruct",
    "notes": "Fireworks AI production model serving"
  },
  {
    "name": "OpenRouter",
    "category": "router",
    "base_url": "https://openrouter.ai/api/v1",
    "format": "openai",
    "default_model": "auto",
    "notes": "OpenRouter unified multi-provider gateway"
  },
  {
    "name": "Novita AI",
    "category": "fast",
    "base_url": "https://api.novita.ai/v3/openai",
    "format": "openai",
    "default_model": "meta-llama/llama-3.3-70b-instruct",
    "notes": "Novita AI serverless LLM GPU cloud"
  },
  {
    "name": "Hyperbolic",
    "category": "fast",
    "base_url": "https://api.hyperbolic.xyz/v1",
    "format": "openai",
    "default_model": "meta-llama/Llama-3.3-70B-Instruct",
    "notes": "Hyperbolic decentralized GPU network"
  },
  {
    "name": "SiliconFlow (SiliconCloud)",
    "category": "asian",
    "base_url": "https://api.siliconflow.cn/v1",
    "format": "openai",
    "default_model": "deepseek-ai/DeepSeek-V3",
    "notes": "SiliconFlow high-speed AI inference platform"
  },
  {
    "name": "Nebius AI Studio",
    "category": "cloud",
    "base_url": "https://api.studio.nebius.ai/v1",
    "format": "openai",
    "default_model": "meta-llama/Meta-Llama-3.3-70B-Instruct",
    "notes": "Nebius Cloud AI inference"
  },
  {
    "name": "DeepInfra",
    "category": "fast",
    "base_url": "https://api.deepinfra.com/v1/openai",
    "format": "openai",
    "default_model": "meta-llama/Llama-3.3-70B-Instruct",
    "notes": "DeepInfra scalable ML deployment"
  },
  {
    "name": "Anyscale Endpoints",
    "category": "cloud",
    "base_url": "https://api.endpoints.anyscale.com/v1",
    "format": "openai",
    "default_model": "meta-llama/Llama-3.3-70B-Instruct",
    "notes": "Anyscale Ray-powered LLM endpoints"
  },

  // ── Asian & International AI Leaders (21-45) ────────────────────────
  {
    "name": "Moonshot AI (Kimi)",
    "category": "asian",
    "base_url": "https://api.moonshot.cn/v1",
    "format": "openai",
    "default_model": "moonshot-v1-8k",
    "notes": "Kimi Moonshot AI long-context API"
  },
  {
    "name": "Zhipu AI (GLM)",
    "category": "asian",
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "format": "openai",
    "default_model": "glm-4-plus",
    "notes": "Zhipu AI GLM-4 flagship models"
  },
  {
    "name": "Alibaba DashScope (Qwen)",
    "category": "asian",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "format": "openai",
    "default_model": "qwen-max",
    "notes": "Alibaba Qwen series models"
  },
  {
    "name": "Baidu Qianfan (Ernie)",
    "category": "asian",
    "base_url": "https://qianfan.baidubce.com/v2",
    "format": "openai",
    "default_model": "ernie-4.0-8k-latest",
    "notes": "Baidu Ernie Bot platform"
  },
  {
    "name": "Tencent Hunyuan",
    "category": "asian",
    "base_url": "https://api.hunyuan.cloud.tencent.com/v1",
    "format": "openai",
    "default_model": "hunyuan-pro",
    "notes": "Tencent Hunyuan AI models"
  },
  {
    "name": "ByteDance Doubao (Volcengine)",
    "category": "asian",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "format": "openai",
    "default_model": "doubao-pro-128k",
    "notes": "ByteDance Volcengine Doubao LLM"
  },
  {
    "name": "01.AI (Yi)",
    "category": "asian",
    "base_url": "https://api.lingyiwanwu.com/v1",
    "format": "openai",
    "default_model": "yi-lightning",
    "notes": "01.AI Yi series models by Kai-Fu Lee"
  },
  {
    "name": "Baichuan AI",
    "category": "asian",
    "base_url": "https://api.baichuan-ai.com/v1",
    "format": "openai",
    "default_model": "Baichuan4",
    "notes": "Baichuan AI enterprise models"
  },
  {
    "name": "MiniMax",
    "category": "asian",
    "base_url": "https://api.minimax.chat/v1",
    "format": "openai",
    "default_model": "abab6.5t-chat",
    "notes": "MiniMax multimodal AI API"
  },
  {
    "name": "StepFun (Jieyue)",
    "category": "asian",
    "base_url": "https://api.stepfun.com/v1",
    "format": "openai",
    "default_model": "step-1v-8k",
    "notes": "StepFun Step-1 multimodal LLM"
  },
  {
    "name": "Upstage AI (Solar)",
    "category": "asian",
    "base_url": "https://api.upstage.ai/v1/solar",
    "format": "openai",
    "default_model": "solar-pro",
    "notes": "Upstage Solar Pro reasoning LLM"
  },
  {
    "name": "Inflection AI",
    "category": "cloud",
    "base_url": "https://api.inflection.ai/v1",
    "format": "openai",
    "default_model": "inflection-3-pi",
    "notes": "Inflection AI Pi assistant engine"
  },
  {
    "name": "AI21 Labs (Jamba)",
    "category": "cloud",
    "base_url": "https://api.ai21.com/v1",
    "format": "openai",
    "default_model": "jamba-1.5-large",
    "notes": "AI21 Jamba SSM-Transformer hybrid models"
  },
  {
    "name": "Voyage AI",
    "category": "cloud",
    "base_url": "https://api.voyageai.com/v1",
    "format": "openai",
    "default_model": "voyage-3-large",
    "notes": "Voyage AI specialized embedding & rerank models"
  },
  {
    "name": "Jina AI",
    "category": "cloud",
    "base_url": "https://api.jina.ai/v1",
    "format": "openai",
    "default_model": "jina-embeddings-v3",
    "notes": "Jina AI search & embedding foundation models"
  },
  {
    "name": "FriendliAI",
    "category": "fast",
    "base_url": "https://inference.friendli.ai/v1",
    "format": "openai",
    "default_model": "meta-llama-3.3-70b-instruct",
    "notes": "FriendliAI high-throughput serving"
  },
  {
    "name": "Scaleway AI Inference",
    "category": "cloud",
    "base_url": "https://api.scaleway.com/ai-inference/v1",
    "format": "openai",
    "default_model": "llama-3.3-70b-instruct",
    "notes": "Scaleway European sovereign AI cloud"
  },
  {
    "name": "OVHcloud AI Endpoints",
    "category": "cloud",
    "base_url": "https://api.ovh.com/v1/ai",
    "format": "openai",
    "default_model": "meta-llama-3-70b-instruct",
    "notes": "OVHcloud European cloud AI endpoints"
  },
  {
    "name": "Lepton AI",
    "category": "fast",
    "base_url": "https://api.lepton.ai/v1",
    "format": "openai",
    "default_model": "llama3-3-70b-instruct",
    "notes": "Lepton AI 1-line AI deployment"
  },
  {
    "name": "OctoAI (DigitalOcean)",
    "category": "cloud",
    "base_url": "https://text.octoai.run/v1",
    "format": "openai",
    "default_model": "meta-llama-3.3-70b-instruct",
    "notes": "OctoAI compute service by DigitalOcean"
  },
  {
    "name": "Replicate",
    "category": "cloud",
    "base_url": "https://api.replicate.com/v1",
    "format": "openai",
    "default_model": "meta/llama-2-70b-chat",
    "notes": "Replicate cloud model hosting"
  },
  {
    "name": "Hugging Face Inference",
    "category": "cloud",
    "base_url": "https://api-inference.huggingface.co/v1",
    "format": "openai",
    "default_model": "meta-llama/Llama-3.3-70B-Instruct",
    "notes": "Hugging Face Serverless Inference API"
  },
  {
    "name": "Baseten",
    "category": "cloud",
    "base_url": "https://model-baseten.api.baseten.co/v1",
    "format": "openai",
    "default_model": "llama-3-70b-instruct",
    "notes": "Baseten custom model serving infrastructure"
  },
  {
    "name": "RunPod Serverless",
    "category": "fast",
    "base_url": "https://api.runpod.ai/v2/openai/v1",
    "format": "openai",
    "default_model": "meta-llama/Llama-3.3-70B-Instruct",
    "notes": "RunPod distributed GPU cloud serverless API"
  },
  {
    "name": "Modal Labs",
    "category": "cloud",
    "base_url": "https://api.modal.run/v1",
    "format": "openai",
    "default_model": "meta-llama-3.3-70b-instruct",
    "notes": "Modal serverless Python cloud infrastructure"
  },

  // ── Specialty, Router & Gateway Platforms (46-75) ───────────────────
  {
    "name": "Unify AI",
    "category": "router",
    "base_url": "https://api.unify.ai/v1",
    "format": "openai",
    "default_model": "llama-3.3-70b-instruct@groq",
    "notes": "Unify AI LLM router across providers"
  },
  {
    "name": "Martian AI",
    "category": "router",
    "base_url": "https://api.withmartian.com/v1",
    "format": "openai",
    "default_model": "router",
    "notes": "Martian Model Router dynamic LLM allocation"
  },
  {
    "name": "NotDiamond Router",
    "category": "router",
    "base_url": "https://api.notdiamond.ai/v1",
    "format": "openai",
    "default_model": "notdiamond-auto",
    "notes": "NotDiamond AI intelligent model routing"
  },
  {
    "name": "OpenPipe",
    "category": "router",
    "base_url": "https://api.openpipe.ai/v1",
    "format": "openai",
    "default_model": "openpipe-default",
    "notes": "OpenPipe fine-tuning & inference pipeline"
  },
  {
    "name": "Braintrust AI Proxy",
    "category": "router",
    "base_url": "https://api.braintrust.dev/v1",
    "format": "openai",
    "default_model": "gpt-4o",
    "notes": "Braintrust AI proxy & evaluation suite"
  },
  {
    "name": "Portkey AI Gateway",
    "category": "router",
    "base_url": "https://api.portkey.ai/v1",
    "format": "openai",
    "default_model": "gpt-4o",
    "notes": "Portkey enterprise AI gateway & observability"
  },
  {
    "name": "Helicone AI Proxy",
    "category": "router",
    "base_url": "https://oai.h3loud.com/v1",
    "format": "openai",
    "default_model": "gpt-4o",
    "notes": "Helicone open-source LLM observability proxy"
  },
  {
    "name": "LiteLLM Proxy",
    "category": "router",
    "base_url": "http://localhost:4000/v1",
    "format": "openai",
    "default_model": "gpt-4o",
    "notes": "LiteLLM local unified OpenAI-compatible proxy"
  },
  {
    "name": "AIPI Multiple Models Router",
    "category": "router",
    "base_url": "http://localhost:11434/v1",
    "format": "auto",
    "default_model": "auto/best-coding",
    "notes": "AIPI Multiple Models Router with enhanced fixations & zero-downtime failover"
  },
  {
    "name": "Hermes Gateway",
    "category": "router",
    "base_url": "http://localhost:11434/v1",
    "format": "auto",
    "default_model": "gpt-4o",
    "notes": "Hermes Agent standard local Python API gateway"
  },
  {
    "name": "Featherless AI",
    "category": "cloud",
    "base_url": "https://api.featherless.ai/v1",
    "format": "openai",
    "default_model": "meta-llama/Llama-3.3-70B-Instruct",
    "notes": "Featherless AI 2,000+ open-source model library"
  },
  {
    "name": "Chutes AI",
    "category": "fast",
    "base_url": "https://chutes.ai/v1",
    "format": "openai",
    "default_model": "meta-llama/Llama-3.3-70B-Instruct",
    "notes": "Chutes decentralized GPU compute network"
  },
  {
    "name": "Glhf.chat",
    "category": "cloud",
    "base_url": "https://glhf.chat/api/openai/v1",
    "format": "openai",
    "default_model": "hf:meta-llama/Llama-3.3-70B-Instruct",
    "notes": "GLHF community hosted open models"
  },
  {
    "name": "Infermatic AI",
    "category": "cloud",
    "base_url": "https://api.infermatic.ai/v1",
    "format": "openai",
    "default_model": "Llama-3-70B-Instruct",
    "notes": "Infermatic AI open-weight LLM API"
  },
  {
    "name": "Kluster AI",
    "category": "fast",
    "base_url": "https://api.kluster.ai/v1",
    "format": "openai",
    "default_model": "klusterai/Meta-Llama-3.1-405B-Instruct-FP8",
    "notes": "Kluster AI high-performance GPU cluster"
  },
  {
    "name": "MonsterAPI",
    "category": "cloud",
    "base_url": "https://api.monsterapi.ai/v1",
    "format": "openai",
    "default_model": "llama-3-70b-instruct",
    "notes": "MonsterAPI low-cost fine-tuning & inference"
  },
  {
    "name": "Lambda Labs",
    "category": "cloud",
    "base_url": "https://api.lambdalabs.com/v1",
    "format": "openai",
    "default_model": "hermes-3-llama-3.1-405b-fp8",
    "notes": "Lambda Cloud GPU LLM serving"
  },
  {
    "name": "CoreWeave AI",
    "category": "cloud",
    "base_url": "https://api.coreweave.com/v1",
    "format": "openai",
    "default_model": "llama-3.3-70b-instruct",
    "notes": "CoreWeave specialized AI cloud platform"
  },
  {
    "name": "Hetzner AI Endpoint",
    "category": "cloud",
    "base_url": "https://api.hetzner.com/v1",
    "format": "openai",
    "default_model": "llama-3.3-70b",
    "notes": "Hetzner Dedicated Cloud GPU LLM Endpoint"
  },
  {
    "name": "Predibase",
    "category": "cloud",
    "base_url": "https://serving.app.predibase.com/v1",
    "format": "openai",
    "default_model": "llama-3-3-70b-instruct",
    "notes": "Predibase developer platform for fine-tuned LLMs"
  },
  {
    "name": "Clarifai AI",
    "category": "cloud",
    "base_url": "https://api.clarifai.com/v2",
    "format": "openai",
    "default_model": "llama-3-70b-instruct",
    "notes": "Clarifai full-stack computer vision & LLM platform"
  },
  {
    "name": "Salad Cloud",
    "category": "cloud",
    "base_url": "https://api.salad.com/v1",
    "format": "openai",
    "default_model": "llama-3-70b",
    "notes": "Salad Cloud distributed node GPU network"
  },
  {
    "name": "Pipeline AI",
    "category": "cloud",
    "base_url": "https://api.pipeline.ai/v1",
    "format": "openai",
    "default_model": "llama-3-70b",
    "notes": "Pipeline AI serverless execution engine"
  },
  {
    "name": "FluidStack Compute",
    "category": "cloud",
    "base_url": "https://api.fluidstack.io/v1",
    "format": "openai",
    "default_model": "llama-3.3-70b",
    "notes": "FluidStack global low-cost GPU cloud"
  },
  {
    "name": "Paperspace Gradient",
    "category": "cloud",
    "base_url": "https://api.paperspace.com/v1",
    "format": "openai",
    "default_model": "llama-3-70b",
    "notes": "DigitalOcean Paperspace AI cloud platform"
  },
  {
    "name": "Genesis Cloud",
    "category": "cloud",
    "base_url": "https://api.genesiscloud.com/v1",
    "format": "openai",
    "default_model": "llama-3.3-70b",
    "notes": "Genesis Cloud 100% green energy GPU cloud"
  },
  {
    "name": "Cudo Compute",
    "category": "cloud",
    "base_url": "https://api.cudocompute.com/v1",
    "format": "openai",
    "default_model": "llama-3-70b",
    "notes": "Cudo Compute decentralized infrastructure platform"
  },
  {
    "name": "Vercel AI Gateway",
    "category": "router",
    "base_url": "https://ai.vercel.app/v1",
    "format": "openai",
    "default_model": "gpt-4o",
    "notes": "Vercel AI SDK unified cloud gateway"
  },
  {
    "name": "Cloudflare Workers AI",
    "category": "cloud",
    "base_url": "https://api.cloudflare.com/client/v4/ai/v1",
    "format": "openai",
    "default_model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "notes": "Cloudflare edge AI inference engine"
  },
  {
    "name": "Fastly AI Accelerator",
    "category": "cloud",
    "base_url": "https://api.fastly.com/v1",
    "format": "openai",
    "default_model": "llama-3-70b",
    "notes": "Fastly edge AI acceleration platform"
  },

  // ── Local Engine Runtimes & Local Hosts (76-110) ────────────────────
  {
    "name": "Ollama (Local)",
    "category": "local",
    "base_url": "http://localhost:11434/v1",
    "format": "openai",
    "default_model": "llama3.3",
    "notes": "Local Ollama server (Zero API key needed)"
  },
  {
    "name": "LM Studio",
    "category": "local",
    "base_url": "http://localhost:1234/v1",
    "format": "openai",
    "default_model": "local-model",
    "notes": "Local LM Studio desktop server"
  },
  {
    "name": "Jan.ai (Local)",
    "category": "local",
    "base_url": "http://localhost:1337/v1",
    "format": "openai",
    "default_model": "tinyllama",
    "notes": "Jan.ai open-source local desktop AI"
  },
  {
    "name": "LocalAI",
    "category": "local",
    "base_url": "http://localhost:8080/v1",
    "format": "openai",
    "default_model": "gpt-4",
    "notes": "LocalAI self-hosted OpenAI alternative"
  },
  {
    "name": "vLLM (Local)",
    "category": "local",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "meta-llama/Llama-3.3-70B-Instruct",
    "notes": "High-throughput vLLM local serving"
  },
  {
    "name": "llama.cpp Server",
    "category": "local",
    "base_url": "http://localhost:8080/v1",
    "format": "openai",
    "default_model": "ggml-model",
    "notes": "llama-cpp-python / llama-server HTTP daemon"
  },
  {
    "name": "KoboldCPP Engine",
    "category": "local",
    "base_url": "http://localhost:5001/v1",
    "format": "openai",
    "default_model": "kobold-model",
    "notes": "KoboldCPP C++ GGUF local inference server"
  },
  {
    "name": "TabbyAPI ExLlamaV2",
    "category": "local",
    "base_url": "http://localhost:5000/v1",
    "format": "openai",
    "default_model": "exl2-model",
    "notes": "TabbyAPI fast EXL2 GPU model server"
  },
  {
    "name": "Text Generation Inference (TGI)",
    "category": "local",
    "base_url": "http://localhost:8080/v1",
    "format": "openai",
    "default_model": "tgi-model",
    "notes": "Hugging Face TGI production container"
  },
  {
    "name": "Aphrodite Engine",
    "category": "local",
    "base_url": "http://localhost:2242/v1",
    "format": "openai",
    "default_model": "aphrodite-model",
    "notes": "Aphrodite Engine PyTorch LLM server"
  },
  {
    "name": "SGLang Serving",
    "category": "local",
    "base_url": "http://localhost:30000/v1",
    "format": "openai",
    "default_model": "sglang-model",
    "notes": "SGLang RadixAttention fast serving engine"
  },
  {
    "name": "Text Generation WebUI (Oobabooga)",
    "category": "local",
    "base_url": "http://localhost:5000/v1",
    "format": "openai",
    "default_model": "textgen-model",
    "notes": "Oobabooga text-generation-webui extension API"
  },
  {
    "name": "GPT4All Desktop",
    "category": "local",
    "base_url": "http://localhost:4891/v1",
    "format": "openai",
    "default_model": "gpt4all-model",
    "notes": "Nomic GPT4All local desktop app API"
  },
  {
    "name": "FastChat Controller",
    "category": "local",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "vicuna-13b",
    "notes": "LMSYS FastChat open model serving platform"
  },
  {
    "name": "TensorRT-LLM Triton Server",
    "category": "local",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "trt-llm-model",
    "notes": "NVIDIA TensorRT-LLM Triton C++ server"
  },
  {
    "name": "Mindie Server (Huawei Ascend)",
    "category": "local",
    "base_url": "http://localhost:1025/v1",
    "format": "openai",
    "default_model": "ascend-model",
    "notes": "Huawei Mindie Ascend NPU inference engine"
  },
  {
    "name": "KServe ML Inference",
    "category": "local",
    "base_url": "http://localhost:8080/v1",
    "format": "openai",
    "default_model": "kserve-model",
    "notes": "Kubernetes KServe cloud-native model serving"
  },
  {
    "name": "BentoML LLM Server",
    "category": "local",
    "base_url": "http://localhost:3000/v1",
    "format": "openai",
    "default_model": "bentoml-model",
    "notes": "BentoML OpenLLM microservice runtime"
  },
  {
    "name": "Ray Serve LLM Cluster",
    "category": "local",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "ray-serve-model",
    "notes": "Anyscale Ray Serve scalable Python cluster"
  },
  {
    "name": "Triton Inference Server",
    "category": "local",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "triton-model",
    "notes": "NVIDIA Triton multi-framework inference server"
  },
  {
    "name": "TorchServe Engine",
    "category": "local",
    "base_url": "http://localhost:8080/v1",
    "format": "openai",
    "default_model": "torchserve-model",
    "notes": "PyTorch TorchServe official model handler"
  },
  {
    "name": "MLflow Deployments Server",
    "category": "local",
    "base_url": "http://localhost:5000/v1",
    "format": "openai",
    "default_model": "mlflow-model",
    "notes": "Databricks MLflow Gateway deployment server"
  },
  {
    "name": "Runhouse Serving",
    "category": "local",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "runhouse-model",
    "notes": "Runhouse Python compute infrastructure"
  },
  {
    "name": "Axolotl Serving",
    "category": "local",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "axolotl-model",
    "notes": "Axolotl fine-tuning & evaluation server"
  },
  {
    "name": "Unsloth Inference Engine",
    "category": "local",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "unsloth-model",
    "notes": "Unsloth 5x faster 80% less VRAM local inference"
  },
  {
    "name": "Vast.ai Instance Endpoint",
    "category": "cloud",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "vast-model",
    "notes": "Vast.ai GPU instance direct endpoint"
  },
  {
    "name": "JarvisLabs GPU Server",
    "category": "cloud",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "jarvis-model",
    "notes": "JarvisLabs cloud GPU instance server"
  },
  {
    "name": "TensorDock Instance",
    "category": "cloud",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "tensordock-model",
    "notes": "TensorDock low-cost cloud GPU server"
  },

  // ── Developer Applications & Agent Web Interfaces (111-135) ────────
  {
    "name": "Dify AI Platform",
    "category": "apps",
    "base_url": "https://api.dify.ai/v1",
    "format": "openai",
    "default_model": "dify-app",
    "notes": "Dify open-source LLM app development platform"
  },
  {
    "name": "Flowise AI",
    "category": "apps",
    "base_url": "http://localhost:3000/api/v1",
    "format": "openai",
    "default_model": "flowise-flow",
    "notes": "Flowise drag & drop UI for LangChain"
  },
  {
    "name": "Langflow Server",
    "category": "apps",
    "base_url": "http://localhost:7860/api/v1",
    "format": "openai",
    "default_model": "langflow-flow",
    "notes": "Langflow visual framework for AI agents"
  },
  {
    "name": "AnythingLLM",
    "category": "apps",
    "base_url": "http://localhost:3001/api/v1",
    "format": "openai",
    "default_model": "anythingllm-workspace",
    "notes": "AnythingLLM desktop workspace API"
  },
  {
    "name": "Open WebUI",
    "category": "apps",
    "base_url": "http://localhost:3000/api/v1",
    "format": "openai",
    "default_model": "open-webui-model",
    "notes": "Open WebUI self-hosted ChatGPT interface"
  },
  {
    "name": "LibreChat",
    "category": "apps",
    "base_url": "http://localhost:3080/api",
    "format": "openai",
    "default_model": "librechat-model",
    "notes": "LibreChat open-source AI conversation platform"
  },
  {
    "name": "Lobe Chat",
    "category": "apps",
    "base_url": "http://localhost:3210/v1",
    "format": "openai",
    "default_model": "lobe-model",
    "notes": "Lobe Chat modern agent framework UI"
  },
  {
    "name": "NextChat",
    "category": "apps",
    "base_url": "http://localhost:3000/v1",
    "format": "openai",
    "default_model": "nextchat-model",
    "notes": "ChatGPT Next Web lightweight frontend"
  },
  {
    "name": "SillyTavern Server",
    "category": "apps",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "st-model",
    "notes": "SillyTavern advanced character LLM interface"
  },
  {
    "name": "Faraday AI",
    "category": "apps",
    "base_url": "http://localhost:11437/v1",
    "format": "openai",
    "default_model": "faraday-model",
    "notes": "Faraday desktop offline LLM app"
  },
  {
    "name": "Backroom AI",
    "category": "apps",
    "base_url": "http://localhost:8080/v1",
    "format": "openai",
    "default_model": "backroom-model",
    "notes": "Backroom AI agent simulation server"
  },
  {
    "name": "LangServe App",
    "category": "apps",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "langserve-chain",
    "notes": "LangChain LangServe REST deployment"
  },
  {
    "name": "LlamaIndex Service",
    "category": "apps",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "llamaindex-query-engine",
    "notes": "LlamaIndex data framework REST service"
  },
  {
    "name": "Haystack Pipeline Server",
    "category": "apps",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "haystack-pipeline",
    "notes": "deepset Haystack search & RAG pipeline"
  },
  {
    "name": "Semantic Kernel Gateway",
    "category": "apps",
    "base_url": "http://localhost:5000/v1",
    "format": "openai",
    "default_model": "sk-plugin",
    "notes": "Microsoft Semantic Kernel AI gateway"
  },
  {
    "name": "PromptFlow Endpoint",
    "category": "apps",
    "base_url": "http://localhost:8080/v1",
    "format": "openai",
    "default_model": "promptflow-flow",
    "notes": "Microsoft Azure PromptFlow execution endpoint"
  },
  {
    "name": "Agenta AI Server",
    "category": "apps",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "agenta-prompt",
    "notes": "Agenta open-source LLMOps platform"
  },
  {
    "name": "Pezzo AI Platform",
    "category": "apps",
    "base_url": "http://localhost:3000/v1",
    "format": "openai",
    "default_model": "pezzo-prompt",
    "notes": "Pezzo developer-first LLM management platform"
  },
  {
    "name": "Lunary / LLMonitor",
    "category": "apps",
    "base_url": "https://api.lunary.ai/v1",
    "format": "openai",
    "default_model": "lunary-prompt",
    "notes": "Lunary LLM observability & telemetry platform"
  },
  {
    "name": "Honeyhive AI",
    "category": "apps",
    "base_url": "https://api.honeyhive.ai/v1",
    "format": "openai",
    "default_model": "honeyhive-model",
    "notes": "Honeyhive AI evaluation & monitoring"
  },
  {
    "name": "Promptable AI",
    "category": "apps",
    "base_url": "https://api.promptable.ai/v1",
    "format": "openai",
    "default_model": "promptable-model",
    "notes": "Promptable AI engineering tools"
  },
  {
    "name": "OpenLIT Gateway",
    "category": "apps",
    "base_url": "http://localhost:8080/v1",
    "format": "openai",
    "default_model": "openlit-model",
    "notes": "OpenLIT OpenTelemetry LLM monitoring"
  },
  {
    "name": "Traceloop OpenInference",
    "category": "apps",
    "base_url": "http://localhost:4318/v1",
    "format": "openai",
    "default_model": "traceloop-model",
    "notes": "Traceloop OTEL OpenInference SDK collector"
  },

  // ── Enterprise Platforms & Coding IDEs (136-169+) ───────────────────
  {
    "name": "AWS Bedrock (Proxy)",
    "category": "enterprise",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "notes": "Amazon Bedrock via local OpenAI proxy adapter"
  },
  {
    "name": "Azure OpenAI Service",
    "category": "enterprise",
    "base_url": "https://YOUR_RESOURCE.openai.azure.com/openai/deployments/YOUR_DEPLOYMENT",
    "format": "openai",
    "default_model": "gpt-4o",
    "notes": "Microsoft Azure OpenAI enterprise instance"
  },
  {
    "name": "Google Vertex AI (Express Proxy)",
    "category": "enterprise",
    "base_url": "http://localhost:8080/v1",
    "format": "openai",
    "default_model": "gemini-2.0-flash",
    "notes": "Google Cloud Vertex AI via local OpenAI proxy"
  },
  {
    "name": "Databricks Model Serving",
    "category": "enterprise",
    "base_url": "https://YOUR_DATABRICKS.cloud.databricks.com/serving-endpoints",
    "format": "openai",
    "default_model": "databricks-dbrx-instruct",
    "notes": "Databricks Mosaic AI Model Serving"
  },
  {
    "name": "Snowflake Cortex AI",
    "category": "enterprise",
    "base_url": "https://YOUR_ACCOUNT.snowflakecomputing.com/api/v2/cortex/inference",
    "format": "openai",
    "default_model": "snowflake-arctic",
    "notes": "Snowflake Cortex LLM inference engine"
  },
  {
    "name": "Oracle Cloud Infrastructure AI",
    "category": "enterprise",
    "base_url": "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/v1",
    "format": "openai",
    "default_model": "cohere.command-r-plus",
    "notes": "OCI Generative AI service"
  },
  {
    "name": "IBM watsonx.ai",
    "category": "enterprise",
    "base_url": "https://us-south.ml.cloud.ibm.com/v1",
    "format": "openai",
    "default_model": "ibm/granite-3-8b-instruct",
    "notes": "IBM watsonx enterprise AI platform"
  },
  {
    "name": "SAP Generative AI Hub",
    "category": "enterprise",
    "base_url": "https://api.ai.prod.eu-central-1.aws.ml.hana.ondemand.com/v2",
    "format": "openai",
    "default_model": "gpt-4o",
    "notes": "SAP Business Technology Platform AI Hub"
  },
  {
    "name": "Salesforce Einstein AI Gateway",
    "category": "enterprise",
    "base_url": "https://api.salesforce.com/einstein/ai-gateway/v1",
    "format": "openai",
    "default_model": "einstein-gpt",
    "notes": "Salesforce Einstein Trust Layer gateway"
  },
  {
    "name": "ServiceNow Now Intelligence",
    "category": "enterprise",
    "base_url": "https://api.servicenow.com/v1/ai",
    "format": "openai",
    "default_model": "now-llm",
    "notes": "ServiceNow enterprise workflow AI engine"
  },
  {
    "name": "Supabase Edge Vector AI",
    "category": "enterprise",
    "base_url": "https://YOUR_PROJECT.supabase.co/functions/v1/ai",
    "format": "openai",
    "default_model": "gte-small",
    "notes": "Supabase Edge Functions pgvector AI API"
  },
  {
    "name": "Firebase Genkit Service",
    "category": "enterprise",
    "base_url": "https://us-central1-YOUR_PROJECT.cloudfunctions.net",
    "format": "openai",
    "default_model": "googleai/gemini-2.0-flash",
    "notes": "Firebase Genkit developer framework backend"
  },
  {
    "name": "Continue.dev Local Proxy",
    "category": "apps",
    "base_url": "http://localhost:65433/v1",
    "format": "openai",
    "default_model": "continue-model",
    "notes": "Continue.dev IDE extension local backend"
  },
  {
    "name": "Aider CLI Local Proxy",
    "category": "apps",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "aider-model",
    "notes": "Aider AI pair programming local proxy"
  },
  {
    "name": "Cody Sourcegraph Enterprise",
    "category": "enterprise",
    "base_url": "https://sourcegraph.com/.api/completions/stream",
    "format": "openai",
    "default_model": "cody-pro",
    "notes": "Sourcegraph Cody AI code intelligence API"
  },
  {
    "name": "Supermaven AI",
    "category": "fast",
    "base_url": "https://api.supermaven.com/v1",
    "format": "openai",
    "default_model": "supermaven-v1",
    "notes": "Supermaven ultra-fast code completion engine"
  },
  {
    "name": "Codeium Enterprise",
    "category": "enterprise",
    "base_url": "https://api.codeium.com/v1",
    "format": "openai",
    "default_model": "codeium-default",
    "notes": "Codeium Windsurf code generation engine"
  },
  {
    "name": "Cursor IDE Local Proxy",
    "category": "apps",
    "base_url": "http://localhost:11434/v1",
    "format": "openai",
    "default_model": "cursor-small",
    "notes": "Cursor IDE internal model route"
  },
  {
    "name": "Claude Code CLI Gateway",
    "category": "apps",
    "base_url": "http://localhost:11434/v1",
    "format": "anthropic",
    "default_model": "claude-3-7-sonnet-20250219",
    "notes": "Claude Code CLI Anthropic API backend"
  },
  {
    "name": "AIPI Antigravity Cloud Router",
    "category": "router",
    "base_url": "https://cloudcode-pa.googleapis.com",
    "format": "antigravity",
    "default_model": "antigravity/claude-sonnet-4-6",
    "notes": "AIPI Direct Antigravity multi-model gateway (Claude Sonnet 4.6, Gemini 2.5/3.5, GPT-OSS)"
  },
  {
    "name": "OpenCode CLI Gateway",
    "category": "apps",
    "base_url": "http://localhost:11434/v1",
    "format": "openai",
    "default_model": "hy3-free",
    "notes": "OpenCode CLI standard backend gateway"
  },
  {
    "name": "OpenCode Zen Gateway",
    "category": "cloud",
    "base_url": "https://opencode.ai/zen/v1",
    "format": "openai",
    "default_model": "hy3-free",
    "notes": "OpenCode AI Zen & CLI standard gateway (working models: hy3-free, mimo-v2.5-free, laguna-s-2.1-free)"
  },
  {
    "name": "KiloCode Gateway",
    "category": "router",
    "base_url": "http://localhost:20128/v1",
    "format": "openai",
    "default_model": "kilo-auto",
    "notes": "KiloCode multi-tier AI backend routing"
  },
  {
    "name": "RouteLLM Router",
    "category": "router",
    "base_url": "http://localhost:8000/v1",
    "format": "openai",
    "default_model": "routellm-mf",
    "notes": "LMSYS RouteLLM cost-effective router"
  },
  {
    "name": "LangSmith Telemetry Proxy",
    "category": "enterprise",
    "base_url": "https://api.smith.langchain.com/v1",
    "format": "openai",
    "default_model": "gpt-4o",
    "notes": "LangChain LangSmith LLM tracing proxy"
  },
  {
    "name": "Weights & Biases Prompts",
    "category": "enterprise",
    "base_url": "https://api.wandb.ai/v1",
    "format": "openai",
    "default_model": "gpt-4o",
    "notes": "W&B Prompts experiment tracking proxy"
  },
  {
    "name": "PromptLayer Observability",
    "category": "enterprise",
    "base_url": "https://api.promptlayer.com/v1",
    "format": "openai",
    "default_model": "gpt-4o",
    "notes": "PromptLayer prompt management & logging proxy"
  },
  {
    "name": "Humanloop AI Platform",
    "category": "enterprise",
    "base_url": "https://api.humanloop.com/v1",
    "format": "openai",
    "default_model": "humanloop-prompt",
    "notes": "Humanloop enterprise AI workspace"
  },
  {
    "name": "Vellum AI Platform",
    "category": "enterprise",
    "base_url": "https://api.vellum.ai/v1",
    "format": "openai",
    "default_model": "vellum-deployment",
    "notes": "Vellum production LLM application stack"
  },
  {
    "name": "GitHub Copilot",
    "category": "cloud",
    "base_url": "https://api.githubcopilot.com",
    "format": "openai",
    "default_model": "gpt-4o",
    "notes": "GitHub Copilot via Device OAuth"
  },
  {
    "name": "Claude Code",
    "category": "cloud",
    "base_url": "https://api.anthropic.com",
    "format": "anthropic",
    "default_model": "claude-3-7-sonnet-20250219",
    "notes": "Auto-import Claude Code CLI session"
  },
  {
    "name": "Mistral Codestral",
    "category": "cloud",
    "base_url": "https://codestral.mistral.ai/v1",
    "format": "openai",
    "default_model": "codestral-latest",
    "notes": "Mistral dedicated code generation API"
  }
];
