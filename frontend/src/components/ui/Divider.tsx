import React from "react";

export const Divider = () => {
    return (
        <div className="relative flex items-center w-full py-4 my-2">
            <div className="flex-grow border-t border-[#E5E7EB]"></div>
            <span className="flex-shrink-0 px-3 flex items-center bg-[#F9FAFB] text-[10px] font-medium leading-[15px] tracking-[0.5px] uppercase text-[#99A1AF]">
                Or continue with email
            </span>
            <div className="flex-grow border-t border-[#E5E7EB]"></div>
        </div>
    );
};
