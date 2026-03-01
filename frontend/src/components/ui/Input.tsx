import React from "react";

export interface InputProps
    extends React.InputHTMLAttributes<HTMLInputElement> {
    icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
    ({ className, icon, ...props }, ref) => {
        return (
            <div className="relative flex items-center w-full h-[41.12px] bg-white border border-[#E5E7EB] rounded-[10px]">
                {icon && (
                    <div className="absolute left-[14px] flex items-center justify-center text-[#99A1AF]">
                        {icon}
                    </div>
                )}
                <input
                    ref={ref}
                    className={`flex h-full w-full rounded-[10px] bg-transparent text-sm font-medium text-[#99A1AF] placeholder:text-[#99A1AF] focus:outline-none focus:ring-1 focus:ring-[#101828] focus:border-[#101828] disabled:cursor-not-allowed disabled:opacity-50 ${icon ? "pl-[40px] pr-[16px]" : "px-[16px]"
                        } py-[10px] ${className || ""}`}
                    {...props}
                />
            </div>
        );
    }
);

Input.displayName = "Input";
