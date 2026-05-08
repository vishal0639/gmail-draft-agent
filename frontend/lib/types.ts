export type EmailItem = {
  id: string;
  thread_id: string | null;
  subject: string | null;
  from_addr: string | null;
  snippet: string | null;
  internal_date: string | null;
  label_ids: string[];
};

export type EmailListResponse = {
  items: EmailItem[];
  result_size_estimate?: number | null;
  next_page_token?: string | null;
};

export type EmailDetail = EmailItem & {
  body_text: string | null;
  body_html: string | null;
  message_id_rfc: string | null;
  in_reply_to: string | null;
  references: string | null;
  to_addresses: string | null;
};

export type Draft = {
  id: string;
  user_id: string;
  thread_id: string | null;
  source_message_id: string;
  subject: string;
  body: string;
  tone: string;
  status: string;
  gmail_draft_id: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  /** UTC expiry: pending 24h from creation; after approve, 48h from creation; rejected 24h from dismissal. */
  expires_at?: string | null;
};

export type GoogleAuthUrl = { url: string; state: string };

export type UserPreferences = {
  default_tone: string;
  email_signature: string;
  other: Record<string, unknown> | null;
};
