import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import type { UserPreferences } from "@/lib/types";

interface SettingsState {
  preferences: UserPreferences | null;
}

const initialState: SettingsState = {
  preferences: null,
};

const settingsSlice = createSlice({
  name: "settings",
  initialState,
  reducers: {
    setPreferences: (state, action: PayloadAction<UserPreferences | null>) => {
      state.preferences = action.payload;
    },
  },
});

export const { setPreferences } = settingsSlice.actions;
export default settingsSlice.reducer;
