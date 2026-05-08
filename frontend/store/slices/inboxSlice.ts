import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import type { EmailItem } from "@/lib/types";

export type InboxFilter = "unread" | "recent" | "all";
export type ReplyTone = "formal" | "concise" | "friendly";

interface InboxState {
  filter: InboxFilter;
  rows: EmailItem[];
  selected: EmailItem | null;
  tone: ReplyTone;
  /** Gmail `nextPageToken` for the message list; null when no more pages. */
  nextPageToken: string | null;
}

const initialState: InboxState = {
  filter: "unread",
  rows: [],
  selected: null,
  tone: "concise",
  nextPageToken: null,
};

const inboxSlice = createSlice({
  name: "inbox",
  initialState,
  reducers: {
    setFilter: (state, action: PayloadAction<InboxFilter>) => {
      state.filter = action.payload;
    },
    setRows: (state, action: PayloadAction<EmailItem[]>) => {
      state.rows = action.payload;
    },
    appendRows: (state, action: PayloadAction<EmailItem[]>) => {
      const seen = new Set(state.rows.map((r) => r.id));
      for (const row of action.payload) {
        if (!seen.has(row.id)) {
          state.rows.push(row);
          seen.add(row.id);
        }
      }
    },
    setNextPageToken: (state, action: PayloadAction<string | null>) => {
      state.nextPageToken = action.payload;
    },
    setSelected: (state, action: PayloadAction<EmailItem | null>) => {
      state.selected = action.payload;
    },
    setTone: (state, action: PayloadAction<ReplyTone>) => {
      state.tone = action.payload;
    },
  },
});

export const { setFilter, setRows, appendRows, setNextPageToken, setSelected, setTone } =
  inboxSlice.actions;
export default inboxSlice.reducer;
