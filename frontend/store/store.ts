import { combineReducers, configureStore } from "@reduxjs/toolkit";

import draftsReducer from "@/store/slices/draftsSlice";
import inboxReducer from "@/store/slices/inboxSlice";
import overviewReducer from "@/store/slices/overviewSlice";
import sessionReducer from "@/store/slices/sessionSlice";
import settingsReducer from "@/store/slices/settingsSlice";
import uiReducer from "@/store/slices/uiSlice";

const rootReducer = combineReducers({
  ui: uiReducer,
  session: sessionReducer,
  overview: overviewReducer,
  inbox: inboxReducer,
  drafts: draftsReducer,
  settings: settingsReducer,
});

export function makeStore() {
  return configureStore({
    reducer: rootReducer,
  });
}

export type AppStore = ReturnType<typeof makeStore>;
export type RootState = ReturnType<AppStore["getState"]>;
export type AppDispatch = AppStore["dispatch"];
