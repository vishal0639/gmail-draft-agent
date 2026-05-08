import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

interface SessionState {
  userId: string;
  apiBase: string;
}

const initialState: SessionState = {
  userId: "",
  apiBase: "",
};

const sessionSlice = createSlice({
  name: "session",
  initialState,
  reducers: {
    setUserId: (state, action: PayloadAction<string>) => {
      state.userId = action.payload;
    },
    setApiBase: (state, action: PayloadAction<string>) => {
      state.apiBase = action.payload;
    },
  },
});

export const { setUserId, setApiBase } = sessionSlice.actions;
export default sessionSlice.reducer;
