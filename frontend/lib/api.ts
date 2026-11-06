export type DashboardSummary = {
  brand: string;
  store_name: string;
  site_health: number;
  monthly_visits: number;
  conversion_rate: number;
  revenue: number;
  orders: number;
  lead_score: number;
  active_campaigns: number;
  recent_actions: string[];
};

export type Product = {
  id?: string;
  name: string;
  description: string;
  price: string;
  category: string;
  image_url?: string;
  featured?: boolean;
};

export type PublishedSite = {
  id: string;
  slug: string;
  share_url: string;
  qr_code_url: string;
  business_name: string;
  website: GeneratedWebsite;
  seo: {
    title: string;
    description: string;
    keywords: string;
  };
  published_at: string;
  whatsapp_number: string;
  message: string;
};

export type SubscriptionPlan = {
  code: string;
  name: string;
  price: number;
  currency: string;
  description: string;
  features: string[];
  usage_limits: Record<string, number>;
};

export type SubscriptionStatus = {
  plan_code: string;
  plan_name: string;
  status: string;
  amount_paid: string;
  currency: string;
  started_at: string | null;
  ends_at: string | null;
  usage_limits: Record<string, number>;
  current_usage: {
    businesses: number;
    products: number;
  };
};

export type GeneratedWebsite = {
  business_name: string;
  industry: string;
  language: string;
  tagline: string;
  theme: {
    primary: string;
    secondary: string;
    accent: string;
    hero_gradient: string;
  };
  hero_image_url?: string;
  layout_mode?: "modern" | "classic" | "minimal";
  font_family?: string;
  sections: {
    hero: {
      headline: string;
      description: string;
      cta_primary: string;
      cta_secondary: string;
    };
    about: {
      title: string;
      description: string;
      highlights: string[];
    };
    products: {
      title: string;
      items: Array<{ name: string; description: string; price: string; category?: string; image_url?: string }>;
    };
    contact: {
      title: string;
      phone: string;
      email: string;
      address: string;
      business_hours: string;
    };
  };
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetch(`${API_URL}/dashboard/summary`, {
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard summary: ${response.status}`);
  }

  return response.json();
}

export async function getSubscriptionPlans(): Promise<{ plans: SubscriptionPlan[] }> {
  const response = await fetch(`${API_URL}/subscriptions/plans`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch subscription plans: ${response.status}`);
  }

  return response.json();
}

export async function getCurrentSubscription(token?: string): Promise<SubscriptionStatus> {
  const response = await fetch(`${API_URL}/subscriptions/me`, {
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch subscription status: ${response.status}`);
  }

  return response.json();
}

export async function createPaymentOrder(
  planCode: string,
  token: string,
): Promise<{ order_id: string; amount: number; currency: string; key: string; plan_code: string; mock_mode: boolean }> {
  const response = await fetch(`${API_URL}/payments/create-order`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ plan_code: planCode }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create Razorpay order: ${response.status}`);
  }

  return response.json();
}

export async function verifyPayment(payload: {
  plan_code: string;
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}, token: string): Promise<{ status: string; plan_code: string; verified: boolean }> {
  const response = await fetch(`${API_URL}/payments/verify`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Payment verification failed: ${response.status}`);
  }

  return response.json();
}

export async function generateBusinessWebsite(payload: {
  transcript: string;
  language?: string;
  business_name?: string;
  location?: string;
  industry?: string;
}): Promise<GeneratedWebsite> {
  const response = await fetch(`${API_URL}/voice/process`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Website generation failed: ${response.status}`);
  }

  const result = await response.json();
  return result.website;
}

export async function getProducts(): Promise<Product[]> {
  const response = await fetch(`${API_URL}/products`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch products: ${response.status}`);
  }

  return response.json();
}

export async function createProduct(payload: Omit<Product, "id">): Promise<Product> {
  const response = await fetch(`${API_URL}/products`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to create product: ${response.status}`);
  }

  return response.json();
}

export async function updateProduct(productId: string, payload: Omit<Product, "id">): Promise<Product> {
  const response = await fetch(`${API_URL}/products/${productId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to update product: ${response.status}`);
  }

  return response.json();
}

export async function deleteProduct(productId: string): Promise<{ status: string; id: string }> {
  const response = await fetch(`${API_URL}/products/${productId}`, {
    method: "DELETE",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Failed to delete product: ${response.status}`);
  }

  return response.json();
}

export async function publishWebsite(payload: {
  website: GeneratedWebsite;
  business_name?: string;
  seo_title?: string;
  seo_description?: string;
  message?: string;
}): Promise<PublishedSite> {
  const response = await fetch(`${API_URL}/publish`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to publish website: ${response.status}`);
  }

  return response.json();
}

export async function getPublishedWebsite(slug: string): Promise<PublishedSite> {
  const response = await fetch(`${API_URL}/publish/${slug}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch published site: ${response.status}`);
  }

  return response.json();
}
