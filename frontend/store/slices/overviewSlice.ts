import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

interface OverviewState {
  health: Record<string, unknown> | null;
}

const initialState: OverviewState = {
  health: null,
};

const overviewSlice = createSlice({
  name: "overview",
  initialState,
  reducers: {
    setHealth: (state, action: PayloadAction<Record<string, unknown> | null>) => {
      state.health = action.payload;
    },
  },
});

export const { setHealth } = overviewSlice.actions;
export default overviewSlice.reducer;
