import { setErr, setMsg } from "@/store/slices/uiSlice";
import { useAppDispatch } from "@/store/hooks";

export function useNotify() {
  const dispatch = useAppDispatch();
  return {
    toast: (m: string) => {
      dispatch(setMsg(m));
      setTimeout(() => dispatch(setMsg(null)), 5000);
    },
    onError: (e: unknown) => {
      dispatch(setErr(e instanceof Error ? e.message : String(e)));
    },
  };
}
