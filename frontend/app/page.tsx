"use client";

import { type ChangeEvent, useEffect, useRef, useState } from "react";
import {
  createProduct,
  deleteProduct,
  generateBusinessWebsite,
  getDashboardSummary,
  getProducts,
  publishWebsite,
  type DashboardSummary,
  type GeneratedWebsite,
  type Product,
  type PublishedSite,
  updateProduct,
} from "@/lib/api";

const fallbackSummary: DashboardSummary = {
  brand: "Voice2Store AI",
  store_name: "Your Store",
  site_health: 0,
  monthly_visits: 0,
  conversion_rate: 0,
  revenue: 0,
  orders: 0,
  lead_score: 0,
  active_campaigns: 0,
  recent_actions: [
    "Add your business details to start generating a storefront.",
    "Upload products and publish your website when ready.",
  ],
};

const sidebarItems = [
  "Overview",
  "Storefronts",
  "Voice prompts",
  "Products",
  "Customers",
  "Analytics",
];

const metrics = [
  { label: "Monthly visits", value: "18.4K", change: "+18.2%", tone: "cyan" },
  { label: "Conversion rate", value: "4.8%", change: "+1.4%", tone: "amber" },
  { label: "Revenue", value: "₹2.48L", change: "+9.1%", tone: "green" },
  { label: "Orders", value: "1,260", change: "+22.8%", tone: "violet" },
];

const recentWebsites: Array<{ name: string; category: string; status: string; progress: number; accent: string }> = [];

const voicePrompts = [
  "Describe your business and I’ll generate a storefront for you.",
  "Add my products, pricing, and WhatsApp contact details.",
  "Create a modern local business website with trust-building sections.",
];

const accountSettings = [
  { label: "Website auto-publish", value: "Pending setup" },
  { label: "AI voice sync", value: "Ready" },
  { label: "Lead alerts", value: "Configured" },
  { label: "Billing plan", value: "Not selected" },
];

const voiceLanguages = [
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
  { value: "gu", label: "Gujarati" },
];

const emptyProductForm: Omit<Product, "id"> = {
  name: "",
  description: "",
  price: "",
  category: "Bakery",
  image_url: "",
  featured: false,
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

const starterWebsite: GeneratedWebsite = {
  business_name: "Your Business",
  industry: "default",
  language: "en",
  tagline: "A clean storefront for your local business.",
  theme: {
    primary: "#2563eb",
    secondary: "#38bdf8",
    accent: "#eff6ff",
    hero_gradient: "from-blue-600 via-cyan-500 to-sky-300",
  },
  hero_image_url: "",
  layout_mode: "modern",
  font_family: "Inter, sans-serif",
  sections: {
    hero: {
      headline: "Tell us about your business and we’ll build your storefront.",
      description: "Add your details, products, and local business information to generate a polished website.",
      cta_primary: "Start now",
      cta_secondary: "Learn more",
    },
    about: {
      title: "About Us",
      description: "Add your story, values, and mission to help customers trust your business.",
      highlights: ["Local trust", "Professional presentation", "Clear customer messaging"],
    },
    products: {
      title: "Products & Services",
      items: [],
    },
    contact: {
      title: "Contact",
      phone: "",
      email: "",
      address: "",
      business_hours: "",
    },
  },
};

export default function Home() {
  const [summary, setSummary] = useState<DashboardSummary>(fallbackSummary);
  const [loading, setLoading] = useState(true);
  const [selectedLanguage, setSelectedLanguage] = useState<"en" | "hi" | "gu">("en");
  const [transcriptText, setTranscriptText] = useState("");
  const [statusMessage, setStatusMessage] = useState("Ready to capture your business details.");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [audioUrl, setAudioUrl] = useState("");
  const [generatedWebsite, setGeneratedWebsite] = useState<GeneratedWebsite | null>(starterWebsite);
  const [publishedSite, setPublishedSite] = useState<PublishedSite | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [productForm, setProductForm] = useState<Omit<Product, "id">>(emptyProductForm);
  const [editingProductId, setEditingProductId] = useState<string | null>(null);
  const [aiPrompt, setAiPrompt] = useState("Change my website background to blue.");
  const [previewFont, setPreviewFont] = useState(starterWebsite.font_family ?? "Inter, sans-serif");
  const [layoutMode, setLayoutMode] = useState<"modern" | "classic" | "minimal">(starterWebsite.layout_mode ?? "modern");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    const loadSummary = async () => {
      try {
        const data = await getDashboardSummary();
        setSummary(data);
      } catch (error) {
        console.error("Failed to load dashboard summary", error);
      } finally {
        setLoading(false);
      }
    };

    const loadProducts = async () => {
      try {
        const data = await getProducts();
        setProducts(data);
        if (data.length > 0) {
          setGeneratedWebsite((current) => {
            if (!current) return current;
            return {
              ...current,
              sections: {
                ...current.sections,
                products: {
                  ...current.sections.products,
                  items: data.map((item) => ({
                    name: item.name,
                    description: item.description,
                    price: item.price,
                    category: item.category,
                    image_url: item.image_url,
                  })),
                },
              },
            };
          });
        }
      } catch (error) {
        console.error("Failed to load product catalog", error);
      }
    };

    loadSummary();
    loadProducts();
  }, []);

  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, [audioUrl]);

  const startRecording = async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatusMessage("Microphone access is not supported in this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const options = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? { mimeType: "audio/webm;codecs=opus" }
        : undefined;

      const recorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setAudioUrl((currentUrl) => {
          if (currentUrl) {
            URL.revokeObjectURL(currentUrl);
          }
          return URL.createObjectURL(audioBlob);
        });
        stream.getTracks().forEach((track) => track.stop());
        setStatusMessage("Recording saved. Review and transcribe when ready.");
      };

      recorder.start();
      setIsRecording(true);
      setStatusMessage("Recording... speak clearly and naturally.");
    } catch (error) {
      console.error("Microphone access failed", error);
      setStatusMessage("Microphone permission was denied. Please allow access to continue.");
    }
  };

  const stopRecording = () => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === "inactive") {
      setIsRecording(false);
      return;
    }

    recorder.stop();
    setIsRecording(false);
  };

  const handleTranscribe = async () => {
    if (!audioUrl) {
      setStatusMessage("Record a message before transcribing it.");
      return;
    }

    try {
      setIsTranscribing(true);
      setStatusMessage("Transcribing your voice note using OpenAI...");

      const audioBlob = await fetch(audioUrl).then((blobResponse) => blobResponse.blob());
      const formData = new FormData();
      formData.append("file", audioBlob, "voice-note.webm");
      formData.append("language", selectedLanguage);

      const response = await fetch(`${API_URL}/voice/transcribe`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail ?? "Transcription failed");
      }

      setTranscriptText(data.text || "");
      setStatusMessage("Transcription complete. Edit the text before submitting it.");
    } catch (error) {
      console.error("Transcription failed", error);
      setStatusMessage(error instanceof Error ? error.message : "Unable to transcribe your recording right now.");
    } finally {
      setIsTranscribing(false);
    }
  };

  const handleSubmitTranscript = async () => {
    const trimmed = transcriptText.trim();
    if (!trimmed) {
      setStatusMessage("The transcript is empty. Record or type a message before submitting.");
      return;
    }

    try {
      setIsSubmitting(true);
      setStatusMessage("Sending the transcript for AI website generation...");

      const response = await fetch(`${API_URL}/voice/process`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          transcript: trimmed,
          language: selectedLanguage,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail ?? "Submission failed");
      }

      if (data.website) {
        setGeneratedWebsite(data.website);
        setPreviewFont(data.website.font_family ?? "Inter, sans-serif");
        setLayoutMode(data.website.layout_mode ?? "modern");
      } else {
        const generated = await generateBusinessWebsite({
          transcript: trimmed,
          language: selectedLanguage,
        });
        setGeneratedWebsite(generated);
        setPreviewFont(generated.font_family ?? "Inter, sans-serif");
        setLayoutMode(generated.layout_mode ?? "modern");
      }

      setStatusMessage(data.summary || "Transcript successfully submitted for AI processing.");
    } catch (error) {
      console.error("Transcript submission failed", error);
      setStatusMessage(error instanceof Error ? error.message : "Submission failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePublishWebsite = async () => {
    if (!generatedWebsite) {
      setStatusMessage("Generate a website before publishing it.");
      return;
    }

    try {
      setStatusMessage("Publishing the storefront and generating a shareable URL...");
      const result = await publishWebsite({
        website: generatedWebsite,
        business_name: generatedWebsite.business_name,
        seo_title: `${generatedWebsite.business_name} | Storefront`,
        seo_description: generatedWebsite.sections.hero.description,
        message: `Hi ${generatedWebsite.business_name}! I would like to know more about your products.`,
      });

      setPublishedSite(result);
      setStatusMessage("Storefront published successfully. Share the public URL and QR code.");
    } catch (error) {
      console.error("Website publish failed", error);
      setStatusMessage(error instanceof Error ? error.message : "Unable to publish the storefront right now.");
    }
  };

  const syncWebsiteProducts = (nextProducts: Product[]) => {
    setGeneratedWebsite((current) => {
      if (!current) return current;
      return {
        ...current,
        sections: {
          ...current.sections,
          products: {
            ...current.sections.products,
            items: nextProducts.map((product) => ({
              name: product.name || "New Product",
              description: product.description || "Freshly added item.",
              price: product.price || "Custom",
              category: product.category || current.industry,
              image_url: product.image_url || current.hero_image_url,
            })),
          },
        },
      };
    });
  };

  const updateWebsiteValue = <K extends keyof GeneratedWebsite>(key: K, value: GeneratedWebsite[K]) => {
    setGeneratedWebsite((current) => {
      if (!current) return current;
      return { ...current, [key]: value };
    });
  };

  const updateNestedSectionValue = (
    section: "hero" | "about" | "contact",
    field: string,
    value: string,
  ) => {
    setGeneratedWebsite((current) => {
      if (!current) return current;

      return {
        ...current,
        sections: {
          ...current.sections,
          [section]: {
            ...current.sections[section],
            [field]: value,
          },
        },
      };
    });
  };

  const updateProductField = (index: number, field: "name" | "description" | "price", value: string) => {
    setGeneratedWebsite((current) => {
      if (!current) return current;

      const items = [...current.sections.products.items];
      items[index] = { ...items[index], [field]: value };

      return {
        ...current,
        sections: {
          ...current.sections,
          products: {
            ...current.sections.products,
            items,
          },
        },
      };
    });
  };

  const handleProductImageUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        setProductForm((current) => ({ ...current, image_url: reader.result as string }));
      }
    };
    reader.readAsDataURL(file);
  };

  const handleSaveProduct = async () => {
    const cleaned = {
      ...productForm,
      name: productForm.name.trim(),
      description: productForm.description.trim(),
      price: productForm.price.trim(),
      category: productForm.category.trim() || "General",
      image_url: productForm.image_url?.trim() || "",
    };

    if (!cleaned.name || !cleaned.description || !cleaned.price) {
      setStatusMessage("Please fill in the product name, description, and price before saving.");
      return;
    }

    try {
      let savedProduct: Product;
      if (editingProductId) {
        savedProduct = await updateProduct(editingProductId, cleaned);
      } else {
        savedProduct = await createProduct(cleaned);
      }

      const nextProducts = editingProductId
        ? products.map((product) => (product.id === editingProductId ? savedProduct : product))
        : [savedProduct, ...products];

      setProducts(nextProducts);
      syncWebsiteProducts(nextProducts);
      setProductForm(emptyProductForm);
      setEditingProductId(null);
      setStatusMessage(editingProductId ? "Product updated and synced to your website." : "Product added and published to your storefront.");
    } catch (error) {
      console.error("Product save failed", error);
      setStatusMessage(error instanceof Error ? error.message : "Unable to save the product right now.");
    }
  };

  const handleEditProduct = (product: Product) => {
    setEditingProductId(product.id ?? null);
    setProductForm({
      name: product.name,
      description: product.description,
      price: product.price,
      category: product.category,
      image_url: product.image_url ?? "",
      featured: product.featured ?? false,
    });
  };

  const handleDeleteProduct = async (productId: string) => {
    try {
      await deleteProduct(productId);
      const nextProducts = products.filter((product) => product.id !== productId);
      setProducts(nextProducts);
      syncWebsiteProducts(nextProducts);
      if (editingProductId === productId) {
        setEditingProductId(null);
        setProductForm(emptyProductForm);
      }
      setStatusMessage("Product removed from your inventory and storefront.");
    } catch (error) {
      console.error("Product delete failed", error);
      setStatusMessage(error instanceof Error ? error.message : "Unable to delete the product right now.");
    }
  };

  const applyAiEdit = () => {
    const command = aiPrompt.trim();
    if (!command || !generatedWebsite) return;

    const normalized = command.toLowerCase();
    const nextWebsite = { ...generatedWebsite };

    if (normalized.includes("background") || normalized.includes("theme") || normalized.includes("accent")) {
      const colorMap: Record<string, string> = {
        blue: "#2563eb",
        green: "#16a34a",
        orange: "#f97316",
        red: "#ef4444",
        purple: "#8b5cf6",
        black: "#111827",
      };

      const colorMatch = Object.keys(colorMap).find((color) => normalized.includes(color));
      if (colorMatch) {
        nextWebsite.theme.primary = colorMap[colorMatch];
        nextWebsite.theme.secondary = colorMap[colorMatch];
        nextWebsite.theme.accent = `${colorMap[colorMatch]}22`;
      }
    }

    if (normalized.includes("font")) {
      if (normalized.includes("serif")) {
        nextWebsite.font_family = 'Georgia, "Times New Roman", serif';
      } else if (normalized.includes("modern") || normalized.includes("sans")) {
        nextWebsite.font_family = 'Inter, Arial, sans-serif';
      }
    }

    if (normalized.includes("layout") && (normalized.includes("classic") || normalized.includes("minimal") || normalized.includes("modern"))) {
      if (normalized.includes("classic")) nextWebsite.layout_mode = "classic";
      else if (normalized.includes("minimal")) nextWebsite.layout_mode = "minimal";
      else nextWebsite.layout_mode = "modern";
    }

    const titleMatch = command.match(/(?:title|headline|heading)\s+(?:to|=|:)?\s*['"]?([^'".]+)['"]?/i);
    if (titleMatch && titleMatch[1]) {
      nextWebsite.sections.hero.headline = titleMatch[1].trim();
    }

    const aboutMatch = command.match(/about\s+(?:text|copy|description)\s+(?:to|=|:)?\s*['"]?([^'".]+)['"]?/i);
    if (aboutMatch && aboutMatch[1]) {
      nextWebsite.sections.about.description = aboutMatch[1].trim();
    }

    if (normalized.includes("image")) {
      nextWebsite.hero_image_url = "https://images.unsplash.com/photo-1556740749-887f6717d7e4?auto=format&fit=crop&w=1200&q=80";
    }

    setGeneratedWebsite(nextWebsite);
    setPreviewFont(nextWebsite.font_family ?? "Inter, sans-serif");
    setLayoutMode(nextWebsite.layout_mode ?? "modern");
    setStatusMessage(`Updated the website using: “${command}”`);
  };

  return (
    <main className="min-h-screen bg-[#060b14] text-slate-100">
      <div className="mx-auto flex max-w-[1600px] gap-6 px-4 py-4 md:px-6 lg:px-8">
        <aside className="hidden w-[280px] shrink-0 rounded-[28px] border border-white/10 bg-slate-900/80 p-5 shadow-[0_25px_80px_rgba(15,23,42,0.65)] backdrop-blur-xl lg:block">
          <div className="mb-8 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-400 via-amber-300 to-yellow-200 text-lg font-black text-slate-950 shadow-lg shadow-orange-500/30">
              V
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Workspace</p>
              <h2 className="text-xl font-bold text-white">Voice2Store</h2>
            </div>
          </div>

          <nav className="space-y-2">
            {sidebarItems.map((item, index) => (
              <button
                key={item}
                className={`flex w-full items-center justify-between rounded-2xl px-3 py-2.5 text-left text-sm transition ${
                  index === 0
                    ? "bg-orange-500/15 text-orange-100 ring-1 ring-orange-400/25"
                    : "text-slate-300 hover:bg-slate-800/80 hover:text-white"
                }`}
              >
                <span>{item}</span>
                <span className="rounded-full border border-slate-700 px-1.5 py-0.5 text-[10px] text-slate-400">
                  {String(index + 1).padStart(2, "0")}
                </span>
              </button>
            ))}
          </nav>

          <div className="mt-8 rounded-3xl border border-orange-400/20 bg-gradient-to-br from-orange-500/10 via-slate-900 to-slate-900 p-4">
            <p className="text-[10px] uppercase tracking-[0.24em] text-orange-200/80">AI status</p>
            <div className="mt-3 flex items-end justify-between">
              <p className="text-4xl font-black text-white">{summary.lead_score}</p>
              <span className="rounded-full bg-emerald-500/10 px-2 py-1 text-[10px] font-medium text-emerald-300">
                +12.4%
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-300">Lead generation score</p>
          </div>

          <div className="mt-6 rounded-3xl border border-slate-800 bg-slate-950/60 p-4">
            <p className="text-[10px] uppercase tracking-[0.24em] text-slate-400">Quick stats</p>
            <div className="mt-4 space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Active campaigns</span>
                <span className="font-semibold text-white">{summary.active_campaigns}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Website health</span>
                <span className="font-semibold text-emerald-300">{summary.site_health}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Avg. response</span>
                <span className="font-semibold text-white">12 min</span>
              </div>
            </div>
          </div>
        </aside>

        <div className="flex-1">
          <header className="rounded-[28px] border border-white/10 bg-slate-900/80 p-4 shadow-[0_20px_60px_rgba(15,23,42,0.5)] backdrop-blur-xl md:p-5">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.26em] text-slate-400">Dashboard overview</p>
                <h1 className="mt-2 text-3xl font-black tracking-tight text-white md:text-4xl">
                  {summary.brand}
                </h1>
              </div>

              <div className="flex items-center gap-3">
                <div className="hidden items-center gap-2 rounded-full border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-300 md:flex">
                  <span className="text-slate-500">⌕</span>
                  Search storefronts
                </div>
                <button className="rounded-full border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-100 transition hover:border-slate-500 hover:bg-slate-700">
                  Export report
                </button>
                <button className="rounded-full bg-gradient-to-r from-orange-500 to-amber-400 px-4 py-2 text-sm font-semibold text-slate-950 shadow-lg shadow-orange-500/30 transition hover:brightness-110">
                  + New website
                </button>
              </div>
            </div>
          </header>

          <section className="mt-6 grid gap-6 xl:grid-cols-[1.55fr_0.85fr]">
            <div className="overflow-hidden rounded-[30px] border border-orange-400/20 bg-gradient-to-br from-[#111827] via-[#0f172a] to-[#0b1220] p-5 shadow-[0_25px_80px_rgba(249,115,22,0.10)] md:p-6">
              <div className="mb-5 flex items-center justify-between">
                <div className="inline-flex items-center gap-2 rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.22em] text-orange-200">
                  <span className="h-2 w-2 rounded-full bg-orange-400" />
                  Voice website builder
                </div>
                <span className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-medium text-emerald-300">
                  Live capture
                </span>
              </div>

              <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
                <div>
                  <h2 className="max-w-lg text-3xl font-black tracking-tight text-white md:text-5xl">
                    Create a premium storefront from your voice.
                  </h2>
                  <p className="mt-4 max-w-xl text-sm leading-7 text-slate-300 md:text-base">
                    Describe your business in a few words and let Voice2Store turn it into a tailored, conversion-focused website for your local brand.
                  </p>

                  <div className="mt-6 rounded-[24px] border border-slate-700 bg-slate-950/40 p-4">
                    <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.24em] text-slate-400">Voice capture</p>
                        <div className="mt-2 flex items-center gap-3">
                          <select
                            value={selectedLanguage}
                            onChange={(event) => setSelectedLanguage(event.target.value as "en" | "hi" | "gu")}
                            aria-label="Select language"
                            className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-100 outline-none ring-0"
                          >
                            {voiceLanguages.map((language) => (
                              <option key={language.value} value={language.value}>
                                {language.label}
                              </option>
                            ))}
                          </select>
                          <button
                            onClick={isRecording ? stopRecording : startRecording}
                            disabled={isTranscribing}
                            className={`flex h-11 w-11 items-center justify-center rounded-full text-xl shadow-lg transition ${
                              isRecording
                                ? "bg-red-500 text-white shadow-red-500/30"
                                : "bg-gradient-to-br from-orange-500 to-amber-300 text-slate-950 shadow-orange-500/30"
                            }`}
                          >
                            {isRecording ? "■" : "◉"}
                          </button>
                        </div>
                      </div>

                      <button
                        onClick={handleTranscribe}
                        disabled={isTranscribing || !audioUrl}
                        className="rounded-full border border-orange-500/30 bg-orange-500/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-orange-100 transition hover:bg-orange-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {isTranscribing ? "Transcribing..." : "Transcribe"}
                      </button>
                    </div>

                    {audioUrl && (
                      <div className="mt-4 overflow-hidden rounded-2xl border border-slate-700 bg-slate-900/80 p-3">
                        <audio controls src={audioUrl} className="w-full" />
                      </div>
                    )}

                    <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-900/80 p-3">
                      <label className="text-[10px] uppercase tracking-[0.22em] text-slate-400">Recognized text</label>
                      <textarea
                        value={transcriptText}
                        onChange={(event) => setTranscriptText(event.target.value)}
                        placeholder="Your transcript appears here..."
                        rows={5}
                        className="mt-2 w-full resize-none rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-orange-500/40"
                      />
                    </div>

                    <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <p className="text-xs text-slate-300">{statusMessage}</p>
                      <button
                        onClick={handleSubmitTranscript}
                        disabled={isSubmitting || !transcriptText.trim()}
                        className="rounded-full bg-gradient-to-r from-orange-500 to-amber-400 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {isSubmitting ? "Submitting..." : "Submit for AI"}
                      </button>
                    </div>
                  </div>

                  <div className="mt-5 flex flex-wrap gap-2">
                    {voicePrompts.map((prompt) => (
                      <button
                        key={prompt}
                        className="rounded-full border border-slate-700 bg-slate-900/60 px-3 py-2 text-xs text-slate-200 transition hover:border-orange-500/30 hover:text-white"
                      >
                        {prompt.length > 55 ? `${prompt.slice(0, 55)}…` : prompt}
                      </button>
                    ))}
                  </div>

                  <div className="mt-6 flex flex-wrap gap-3">
                      <button className="rounded-full bg-gradient-to-r from-orange-500 to-amber-400 px-5 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-orange-500/30 transition hover:brightness-110">
                      Build website
                    </button>
                    <button
                      onClick={handlePublishWebsite}
                      className="rounded-full border border-orange-500/30 bg-orange-500/10 px-5 py-3 text-sm font-medium text-orange-100 transition hover:bg-orange-500/20"
                    >
                      Publish site
                    </button>
                  </div>
                </div>

                <div className="flex flex-col justify-between gap-4">
                  <div className="rounded-[26px] border border-slate-800 bg-slate-950/50 p-4">
                    <p className="text-[10px] uppercase tracking-[0.24em] text-slate-400">Website score</p>
                    <div className="mt-4 flex items-end justify-between">
                      <p className="text-4xl font-black text-white">94</p>
                      <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-[10px] font-medium text-emerald-300">
                        +8.6%
                      </span>
                    </div>
                    <div className="mt-4 space-y-2">
                      {[72, 84, 91, 94].map((value, index) => (
                        <div key={value} className="flex items-center gap-2">
                          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-orange-500 to-amber-300"
                              style={{ width: `${value}%`, transitionDelay: `${index * 100}ms` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-[26px] border border-slate-800 bg-slate-950/50 p-4">
                    <p className="text-[10px] uppercase tracking-[0.24em] text-slate-400">Ready to publish</p>
                    <ul className="mt-4 space-y-3 text-sm text-slate-300">
                      {[
                        "Responsive storefront layout",
                        "WhatsApp ordering flow",
                        "Google Business sync",
                      ].map((item) => (
                        <li key={item} className="flex items-center gap-2">
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/15 text-[10px] text-emerald-300">
                            ✓
                          </span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-[30px] border border-white/10 bg-slate-900/80 p-5 shadow-[0_20px_60px_rgba(15,23,42,0.5)]">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.24em] text-slate-400">AI pipeline</p>
                  <h3 className="mt-2 text-xl font-bold text-white">Website creation</h3>
                </div>
                <span className="rounded-full bg-cyan-500/10 px-2.5 py-1 text-[10px] font-medium text-cyan-300">
                  3 minutes
                </span>
              </div>

              <div className="mt-5 space-y-4">
                {[
                  { label: "Business context", value: "Collected" },
                  { label: "Branding", value: "Generated" },
                  { label: "Products", value: "Synced" },
                  { label: "SEO copy", value: "Ready" },
                ].map((item) => (
                  <div key={item.label} className="rounded-2xl border border-slate-800 bg-slate-950/60 p-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-300">{item.label}</span>
                      <span className="font-medium text-emerald-300">{item.value}</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 rounded-2xl border border-dashed border-orange-400/30 bg-orange-500/5 p-4 text-sm text-slate-200">
                <p className="font-medium text-white">Business summary</p>
                <p className="mt-2 leading-6 text-slate-300">
                  Authentic neighborhood bakery with seasonal menu, delivery orders, and a warm brand story built around community and freshness.
                </p>
              </div>
            </div>
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[1.5fr_0.85fr]">
            <div className="rounded-[30px] border border-white/10 bg-slate-900/80 p-5 shadow-[0_20px_60px_rgba(15,23,42,0.5)]">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.24em] text-slate-400">Portfolio</p>
                  <h3 className="mt-2 text-2xl font-bold text-white">Recent websites</h3>
                </div>
                <button className="rounded-full border border-slate-700 bg-slate-950/60 px-3 py-1.5 text-xs font-medium text-slate-200 transition hover:border-slate-500">
                  View all
                </button>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                {recentWebsites.map((site) => (
                  <div key={site.name} className="rounded-[24px] border border-slate-800 bg-slate-950/60 p-4 transition hover:border-orange-500/30 hover:bg-slate-900">
                    <div className={`mb-4 h-28 rounded-2xl bg-gradient-to-br ${site.accent}`} />
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-white">{site.name}</p>
                        <p className="mt-1 text-sm text-slate-400">{site.category}</p>
                      </div>
                      <span className="rounded-full border border-slate-700 px-2 py-1 text-[10px] font-medium text-slate-300">
                        {site.status}
                      </span>
                    </div>
                    <div className="mt-4">
                      <div className="mb-2 flex items-center justify-between text-[11px] uppercase tracking-[0.18em] text-slate-400">
                        <span>Build</span>
                        <span>{site.progress}%</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className={`h-full rounded-full bg-gradient-to-r ${site.accent}`}
                          style={{ width: `${site.progress}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-[30px] border border-white/10 bg-slate-900/80 p-5 shadow-[0_20px_60px_rgba(15,23,42,0.5)]">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.24em] text-slate-400">Account</p>
                  <h3 className="mt-2 text-2xl font-bold text-white">Settings</h3>
                </div>
                <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gradient-to-br from-orange-500 to-amber-300 text-lg text-slate-950">
                  A
                </div>
              </div>

              <div className="mt-5 space-y-3">
                {accountSettings.map((setting) => (
                  <div key={setting.label} className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/60 px-3 py-3">
                    <span className="text-sm text-slate-300">{setting.label}</span>
                    <span className="rounded-full bg-slate-800 px-2.5 py-1 text-[10px] font-medium text-slate-200">
                      {setting.value}
                    </span>
                  </div>
                ))}
              </div>

              <div className="mt-5 rounded-2xl border border-dashed border-slate-700 bg-slate-950/50 p-4">
                <p className="text-sm text-slate-400">Current plan</p>
                <div className="mt-2 flex items-center justify-between">
                  <p className="text-xl font-bold text-white">Growth Suite</p>
                  <span className="rounded-full bg-orange-500/10 px-2 py-1 text-[10px] font-medium text-orange-200">
                    Active
                  </span>
                </div>
              </div>
            </div>
          </section>

          <section className="mt-6 rounded-[30px] border border-white/10 bg-slate-900/80 p-5 shadow-[0_20px_60px_rgba(15,23,42,0.5)]">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <p className="text-[10px] uppercase tracking-[0.24em] text-slate-400">Product management</p>
                <h3 className="mt-2 text-2xl font-bold text-white">Manage storefront inventory</h3>
              </div>
              <span className="rounded-full border border-orange-400/20 bg-orange-500/10 px-2.5 py-1 text-[10px] font-medium text-orange-200">
                {products.length} items
              </span>
            </div>

            <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
              <div className="rounded-[26px] border border-slate-800 bg-slate-950/60 p-4">
                <div className="mb-4 flex items-center justify-between">
                  <p className="text-sm font-semibold text-white">{editingProductId ? "Edit product" : "Add a product"}</p>
                  {editingProductId && (
                    <button
                      onClick={() => {
                        setEditingProductId(null);
                        setProductForm(emptyProductForm);
                      }}
                      className="text-xs text-slate-300 hover:text-white"
                    >
                      Cancel
                    </button>
                  )}
                </div>

                <div className="space-y-3">
                  <label className="block">
                    <span className="mb-1 block text-[10px] uppercase tracking-[0.2em] text-slate-400">Product name</span>
                    <input
                      value={productForm.name}
                      onChange={(event) => setProductForm((current) => ({ ...current, name: event.target.value }))}
                      className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                      placeholder="Signature Cakes"
                    />
                  </label>

                  <label className="block">
                    <span className="mb-1 block text-[10px] uppercase tracking-[0.2em] text-slate-400">Description</span>
                    <textarea
                      rows={3}
                      value={productForm.description}
                      onChange={(event) => setProductForm((current) => ({ ...current, description: event.target.value }))}
                      className="w-full resize-none rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                      placeholder="Handmade celebration cakes for birthdays and gifting."
                    />
                  </label>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <label className="block">
                      <span className="mb-1 block text-[10px] uppercase tracking-[0.2em] text-slate-400">Price</span>
                      <input
                        value={productForm.price}
                        onChange={(event) => setProductForm((current) => ({ ...current, price: event.target.value }))}
                        className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                        placeholder="₹799"
                      />
                    </label>

                    <label className="block">
                      <span className="mb-1 block text-[10px] uppercase tracking-[0.2em] text-slate-400">Category</span>
                      <input
                        value={productForm.category}
                        onChange={(event) => setProductForm((current) => ({ ...current, category: event.target.value }))}
                        className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                        placeholder="Bakery"
                      />
                    </label>
                  </div>

                  <div className="rounded-xl border border-dashed border-slate-700 bg-slate-900/60 p-3">
                    <label className="mb-2 block text-[10px] uppercase tracking-[0.2em] text-slate-400">Product image</label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleProductImageUpload}
                      className="block w-full text-sm text-slate-300 file:mr-3 file:rounded-full file:border-0 file:bg-orange-500/20 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-orange-100"
                    />
                    {productForm.image_url && (
                      <img src={productForm.image_url} alt="Product preview" className="mt-3 h-24 w-full rounded-xl object-cover" />
                    )}
                    <input
                      value={productForm.image_url}
                      onChange={(event) => setProductForm((current) => ({ ...current, image_url: event.target.value }))}
                      className="mt-3 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white outline-none focus:border-orange-500"
                      placeholder="https://images.unsplash.com/..."
                    />
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {Array.from(new Set(products.map((product) => product.category).filter(Boolean))).map((category) => (
                      <button
                        key={category}
                        type="button"
                        onClick={() => setProductForm((current) => ({ ...current, category }))}
                        className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-1 text-[10px] font-medium text-slate-200 hover:border-orange-500/40 hover:text-white"
                      >
                        {category}
                      </button>
                    ))}
                  </div>

                  <button
                    onClick={handleSaveProduct}
                    className="w-full rounded-full bg-gradient-to-r from-orange-500 to-amber-400 px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.18em] text-slate-950"
                  >
                    {editingProductId ? "Update product" : "Add product"}
                  </button>
                </div>
              </div>

              <div className="rounded-[26px] border border-slate-800 bg-slate-950/60 p-4">
                <p className="text-sm font-semibold text-white">Catalog</p>
                <div className="mt-4 grid gap-3">
                  {products.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/40 p-6 text-center text-sm text-slate-400">
                      No products yet. Add your first item to populate the storefront.
                    </div>
                  ) : (
                    products.map((product) => (
                      <div key={product.id ?? product.name} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-3">
                        <div className="flex gap-3">
                          {product.image_url && (
                            <img src={product.image_url} alt={product.name} className="h-16 w-16 rounded-xl object-cover" />
                          )}
                          <div className="min-w-0 flex-1">
                            <div className="flex items-start justify-between gap-3">
                              <div className="min-w-0">
                                <p className="truncate font-semibold text-white">{product.name}</p>
                                <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-orange-200">{product.category}</p>
                              </div>
                              <span className="rounded-full bg-orange-500/10 px-2 py-1 text-[10px] font-medium text-orange-200">
                                {product.price}
                              </span>
                            </div>
                            <p className="mt-2 text-sm leading-6 text-slate-300">{product.description}</p>
                          </div>
                        </div>
                        <div className="mt-3 flex gap-2">
                          <button
                            onClick={() => handleEditProduct(product)}
                            className="rounded-full border border-slate-700 bg-slate-800 px-3 py-1.5 text-[10px] font-medium text-slate-200"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => product.id && handleDeleteProduct(product.id)}
                            className="rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-[10px] font-medium text-red-200"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </section>

          {generatedWebsite && (
            <section className="mt-6 rounded-[30px] border border-white/10 bg-slate-900/80 p-5 shadow-[0_20px_60px_rgba(15,23,42,0.5)]">
              <div className="mb-5 flex items-center justify-between gap-3">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.24em] text-slate-400">Generated website</p>
                  <h3 className="mt-2 text-2xl font-bold text-white">{generatedWebsite.business_name}</h3>
                </div>
                <span className="rounded-full border border-slate-700 px-2.5 py-1 text-[10px] font-medium text-slate-200">
                  {generatedWebsite.industry}
                </span>
              </div>

              {publishedSite && (
                <div className="mb-6 grid gap-4 rounded-[24px] border border-emerald-500/20 bg-emerald-500/5 p-4 lg:grid-cols-[1fr_180px]">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-200">Published URL</p>
                    <a href={publishedSite.share_url} target="_blank" rel="noreferrer" className="mt-2 block break-all text-sm font-medium text-white">
                      {publishedSite.share_url}
                    </a>
                  </div>
                  <div className="flex items-center justify-center">
                    <img src={publishedSite.qr_code_url} alt="QR code" className="h-20 w-20 rounded-xl border border-white/10 bg-white p-2" />
                  </div>
                </div>
              )}

              <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
                <div className="space-y-5">
                  <div
                    className="overflow-hidden rounded-[28px] border border-slate-800"
                    style={{
                      background: `linear-gradient(135deg, ${generatedWebsite.theme.primary}, ${generatedWebsite.theme.secondary})`,
                      fontFamily: previewFont,
                    }}
                  >
                    <div
                      className="relative min-h-[320px] bg-cover bg-center p-6 text-slate-950"
                      style={{
                        backgroundImage: generatedWebsite.hero_image_url ? `url(${generatedWebsite.hero_image_url})` : "none",
                        backgroundBlendMode: "multiply",
                        backgroundColor: generatedWebsite.theme.accent,
                      }}
                    >
                      <div className="absolute inset-0 bg-white/10 backdrop-blur-[1px]" />
                      <div className="relative z-10">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="text-xs uppercase tracking-[0.22em] font-semibold opacity-80">{generatedWebsite.business_name}</p>
                            <h4 className="mt-2 max-w-xl text-3xl font-black leading-tight">{generatedWebsite.sections.hero.headline}</h4>
                          </div>
                          <div className="rounded-full bg-white/20 px-3 py-1 text-xs font-semibold backdrop-blur-sm">
                            {generatedWebsite.language.toUpperCase()}
                          </div>
                        </div>
                        <p className="mt-4 max-w-2xl text-sm leading-6 opacity-90">{generatedWebsite.sections.hero.description}</p>
                        <div className="mt-5 flex gap-3">
                          <button className="rounded-full bg-slate-950 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-white">
                            {generatedWebsite.sections.hero.cta_primary}
                          </button>
                          <button className="rounded-full border border-slate-900/40 bg-white/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-950">
                            {generatedWebsite.sections.hero.cta_secondary}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="grid gap-4 lg:grid-cols-3">
                    <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                      <h4 className="text-lg font-bold text-white">{generatedWebsite.sections.about.title}</h4>
                      <p className="mt-3 text-sm leading-6 text-slate-300">{generatedWebsite.sections.about.description}</p>
                      <ul className="mt-4 space-y-2 text-sm text-slate-200">
                        {generatedWebsite.sections.about.highlights.map((item) => (
                          <li key={item} className="flex items-center gap-2">
                            <span className="inline-block h-2 w-2 rounded-full bg-emerald-400" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4 lg:col-span-2">
                      <h4 className="text-lg font-bold text-white">{generatedWebsite.sections.products.title}</h4>
                      <div className="mt-4 grid gap-3 md:grid-cols-3">
                        {generatedWebsite.sections.products.items.map((item) => (
                          <div key={item.name} className="overflow-hidden rounded-2xl border border-slate-700 bg-slate-900/70 p-3">
                            {item.image_url && (
                              <img src={item.image_url} alt={item.name} className="mb-3 h-28 w-full rounded-xl object-cover" />
                            )}
                            <p className="font-semibold text-white">{item.name}</p>
                            {item.category && (
                              <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-orange-200">{item.category}</p>
                            )}
                            <p className="mt-2 text-sm leading-6 text-slate-300">{item.description}</p>
                            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.12em] text-orange-200">{item.price}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                    <h4 className="text-lg font-bold text-white">{generatedWebsite.sections.contact.title}</h4>
                    <div className="mt-3 grid gap-3 md:grid-cols-3 text-sm text-slate-300">
                      <p><span className="font-medium text-white">Phone:</span> {generatedWebsite.sections.contact.phone}</p>
                      <p><span className="font-medium text-white">Email:</span> {generatedWebsite.sections.contact.email}</p>
                      <p><span className="font-medium text-white">Hours:</span> {generatedWebsite.sections.contact.business_hours}</p>
                    </div>
                    <p className="mt-3 text-sm text-slate-300">{generatedWebsite.sections.contact.address}</p>
                  </div>
                </div>

                <div className="rounded-[28px] border border-slate-800 bg-slate-950/60 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <h4 className="text-lg font-bold text-white">Live editor</h4>
                    <span className="rounded-full border border-slate-700 px-2 py-1 text-[10px] uppercase tracking-[0.14em] text-slate-300">
                      {layoutMode}
                    </span>
                  </div>

                  <div className="mt-4 space-y-4">
                    <label className="block">
                      <span className="mb-1 block text-[10px] uppercase tracking-[0.2em] text-slate-400">Business name</span>
                      <input
                        value={generatedWebsite.business_name}
                        onChange={(e) => updateWebsiteValue("business_name", e.target.value)}
                        className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                      />
                    </label>

                    <label className="block">
                      <span className="mb-1 block text-[10px] uppercase tracking-[0.2em] text-slate-400">Hero headline</span>
                      <input
                        value={generatedWebsite.sections.hero.headline}
                        onChange={(e) => updateNestedSectionValue("hero", "headline", e.target.value)}
                        className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                      />
                    </label>

                    <label className="block">
                      <span className="mb-1 block text-[10px] uppercase tracking-[0.2em] text-slate-400">Hero image URL</span>
                      <input
                        value={generatedWebsite.hero_image_url ?? ""}
                        onChange={(e) => updateWebsiteValue("hero_image_url", e.target.value)}
                        className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                      />
                    </label>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <label className="block">
                        <span className="mb-1 block text-[10px] uppercase tracking-[0.2em] text-slate-400">Primary color</span>
                        <input
                          type="color"
                          value={generatedWebsite.theme.primary}
                          onChange={(e) => {
                            setGeneratedWebsite((current) => current ? { ...current, theme: { ...current.theme, primary: e.target.value } } : current);
                          }}
                          className="h-11 w-full rounded-xl border border-slate-700 bg-slate-900 p-1"
                        />
                      </label>

                      <label className="block">
                        <span className="mb-1 block text-[10px] uppercase tracking-[0.2em] text-slate-400">Secondary color</span>
                        <input
                          type="color"
                          value={generatedWebsite.theme.secondary}
                          onChange={(e) => {
                            setGeneratedWebsite((current) => current ? { ...current, theme: { ...current.theme, secondary: e.target.value } } : current);
                          }}
                          className="h-11 w-full rounded-xl border border-slate-700 bg-slate-900 p-1"
                        />
                      </label>
                    </div>

                    <label className="block">
                      <span className="mb-1 block text-[10px] uppercase tracking-[0.2em] text-slate-400">Font</span>
                      <select
                        value={previewFont}
                        onChange={(e) => {
                          setPreviewFont(e.target.value);
                          setGeneratedWebsite((current) => current ? { ...current, font_family: e.target.value } : current);
                        }}
                        className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                      >
                        <option value="Inter, sans-serif">Modern Sans</option>
                        <option value='Georgia, "Times New Roman", serif'>Classic Serif</option>
                        <option value='"Trebuchet MS", sans-serif'>Rounded UI</option>
                      </select>
                    </label>

                    <label className="block">
                      <span className="mb-1 block text-[10px] uppercase tracking-[0.2em] text-slate-400">Layout style</span>
                      <select
                        value={layoutMode}
                        onChange={(e) => {
                          const nextLayout = e.target.value as "modern" | "classic" | "minimal";
                          setLayoutMode(nextLayout);
                          setGeneratedWebsite((current) => current ? { ...current, layout_mode: nextLayout } : current);
                        }}
                        className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                      >
                        <option value="modern">Modern</option>
                        <option value="classic">Classic</option>
                        <option value="minimal">Minimal</option>
                      </select>
                    </label>

                    <div className="rounded-2xl border border-dashed border-orange-400/30 bg-orange-500/5 p-3">
                      <label className="mb-2 block text-[10px] uppercase tracking-[0.2em] text-slate-400">AI edit prompt</label>
                      <textarea
                        rows={3}
                        value={aiPrompt}
                        onChange={(e) => setAiPrompt(e.target.value)}
                        className="w-full resize-none rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-orange-500"
                        placeholder="Change my website background to blue."
                      />
                      <button
                        onClick={applyAiEdit}
                        className="mt-3 rounded-full bg-gradient-to-r from-orange-500 to-amber-400 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-950"
                      >
                        Apply AI edit
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          )}
        </div>
      </div>

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm">
          <div className="rounded-full border border-orange-500/30 bg-slate-900 px-5 py-3 text-sm text-orange-200">
            Loading dashboard...
          </div>
        </div>
      )}
    </main>
  );
}
