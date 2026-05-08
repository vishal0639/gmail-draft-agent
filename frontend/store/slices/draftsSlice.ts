import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import type { Draft } from "@/lib/types";

interface DraftsState {
  list: Draft[];
  active: Draft | null;
  bodyEd: string;
  idempotencyKey: string;
}

const initialState: DraftsState = {
  list: [],
  active: null,
  bodyEd: "",
  idempotencyKey: "",
};

const draftsSlice = createSlice({
  name: "drafts",
  initialState,
  reducers: {
    setDraftsList: (state, action: PayloadAction<Draft[]>) => {
      state.list = action.payload;
    },
    setActiveDraft: (state, action: PayloadAction<Draft | null>) => {
      const d = action.payload;
      state.active = d;
      state.bodyEd = d ? d.body : "";
    },
    setBodyEd: (state, action: PayloadAction<string>) => {
      state.bodyEd = action.payload;
    },
    setIdempotencyKey: (state, action: PayloadAction<string>) => {
      state.idempotencyKey = action.payload;
    },
    mergeDraft: (state, action: PayloadAction<Draft>) => {
      const d = action.payload;
      state.list = state.list.map((x) => (x.id === d.id ? d : x));
      if (state.active?.id === d.id) {
        state.active = d;
        state.bodyEd = d.body;
      }
    },
  },
});

export const { setDraftsList, setActiveDraft, setBodyEd, setIdempotencyKey, mergeDraft } =
  draftsSlice.actions;
export default draftsSlice.reducer;
