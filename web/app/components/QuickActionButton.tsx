import { LucideIcon } from "lucide-react";
import { motion } from "motion/react";

interface QuickActionButtonProps {
  icon: LucideIcon;
  label: string;
  onClick: () => void;
}

export function QuickActionButton({ icon: Icon, label, onClick }: QuickActionButtonProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="flex flex-col items-center gap-2 p-4 bg-white rounded-xl border-2 border-gray-200 hover:border-green-600 hover:shadow-md transition-all"
    >
      <div className="w-12 h-12 rounded-full bg-green-50 flex items-center justify-center">
        <Icon className="w-6 h-6 text-green-600" />
      </div>
      <span className="text-sm text-gray-700 text-center">{label}</span>
    </motion.button>
  );
}
