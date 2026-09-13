"use client";
import { Menu } from "lucide-react";
import { useEffect, useState } from "react";

const Header = () => {
  const [isAtTop, setIsAtTop] = useState<boolean>(true);

  useEffect(() => {
    const handleScroll = () => {
      setIsAtTop(window.scrollY === 0);
    };

    window.addEventListener("scroll", handleScroll);

    handleScroll();

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header className={`border-b py-4 px-8 flex flex-row justify-between sticky top-0 backdrop-blur-md z-50 ${isAtTop ? "bg-transparent" : "bg-background/70"}`}>
      <div className="text-4xl logo">RedFlags</div>
      <div className="md:hidden flex justify-center items-center">
        <Menu />
      </div>
      <div className="hidden md:flex justify-center items-center"></div>
    </header>
  );
};

export default Header;
 
