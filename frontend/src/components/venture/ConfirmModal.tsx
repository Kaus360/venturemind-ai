import { motion, AnimatePresence } from "framer-motion";
import { type ReactNode } from "react";

export function ConfirmModal({
  open, title, description, confirmLabel = "Confirm", cancelLabel = "Cancel",
  destructive, onConfirm, onClose, children,
}: {
  open: boolean;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  onConfirm: () => void;
  onClose: () => void;
  children?: ReactNode;
}) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-md flex items-center justify-center p-4"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.92, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.92, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="vm-glass max-w-md w-full p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold text-white">{title}</h3>
            {description && <p className="text-sm text-slate-400 mt-2">{description}</p>}
            {children && <div className="mt-4">{children}</div>}
            <div className="flex items-center justify-end gap-2 mt-6">
              <button onClick={onClose} className="px-3 py-1.5 text-sm rounded-md bg-slate-800/70 hover:bg-slate-700/70 text-slate-200 transition">{cancelLabel}</button>
              <button
                onClick={onConfirm}
                className={`px-3 py-1.5 text-sm rounded-md text-white transition hover:scale-[1.03] ${destructive ? "bg-rose-500 hover:bg-rose-400 shadow-lg shadow-rose-500/40" : "bg-indigo-500 hover:bg-indigo-400 shadow-lg shadow-indigo-500/40"}`}
              >{confirmLabel}</button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}