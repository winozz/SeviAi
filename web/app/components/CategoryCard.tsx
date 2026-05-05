import { LucideIcon } from "lucide-react";
import { motion } from "motion/react";

interface CategoryCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  onClick: () => void;
}

export function CategoryCard({ icon: Icon, title, description, onClick }: CategoryCardProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      className="flex items-start gap-4 p-4 bg-white rounded-xl border-2 border-gray-200 hover:border-green-600 hover:shadow-lg transition-all text-left w-full"
    >
      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-green-500 to-green-700 flex items-center justify-center flex-shrink-0">
        <Icon className="w-6 h-6 text-white" />
      </div>
      <div className="flex-1">
        <h3 className="text-base mb-1 text-gray-900">{title}</h3>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
    </motion.button>
  );
}
