import React from "react";

export interface ButtonProps
    extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "default" | "outline";
    icon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = "default", icon, children, ...props }, ref) => {
        const baseStyles =
            "inline-flex items-center justify-center rounded-[10px] text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-1 disabled:pointer-events-none disabled:opacity-50";

        const variants = {
            default: "bg-[#101828] text-white hover:bg-[#101828]/90",
            outline:
                "border border-[#E5E7EB] bg-white text-[#364153] hover:bg-gray-50",
        };

        return (
            <button
                ref={ref}
                className={`${baseStyles} ${variants[variant]} ${className || ""
                    }`}
                {...props}
            >
                {icon && <span className="mr-2 flex items-center">{icon}</span>}
                {children}
            </button>
        );
    }
);

Button.displayName = "Button";
