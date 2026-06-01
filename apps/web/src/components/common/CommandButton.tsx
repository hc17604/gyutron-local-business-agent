import type { LucideIcon } from "lucide-react";

interface CommandButtonProps {
  icon?: LucideIcon;
  label: string;
  description?: string;
  active?: boolean;
  onClick?: () => void;
}

export function CommandButton({ icon: Icon, label, description, active, onClick }: CommandButtonProps) {
  return (
    <button className={active ? "command-button active" : "command-button"} onClick={onClick} type="button">
      {Icon ? <Icon size={16} /> : null}
      <span>
        <strong>{label}</strong>
        {description ? <small>{description}</small> : null}
      </span>
    </button>
  );
}
