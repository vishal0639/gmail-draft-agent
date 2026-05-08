import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

export type Tab = "overview" | "inbox" | "drafts" | "settings";

interface UIState {
  tab: Tab;
  msg: string | null;
  err: string | null;
}

const initialState: UIState = {
  tab: "overview",
  msg: null,
  err: null,
};

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    setTab: (state, action: PayloadAction<Tab>) => {
      state.tab = action.payload;
    },
    setMsg: (state, action: PayloadAction<string | null>) => {
      state.msg = action.payload;
      state.err = null;
    },
    setErr: (state, action: PayloadAction<string | null>) => {
      state.err = action.payload;
      state.msg = null;
    },
    dismissAlert: (state) => {
      state.msg = null;
      state.err = null;
    },
  },
});

export const { setTab, setMsg, setErr, dismissAlert } = uiSlice.actions;
export default uiSlice.reducer;
