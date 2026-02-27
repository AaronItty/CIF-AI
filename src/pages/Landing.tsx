import { useNavigate } from "react-router-dom";
import Spline from '@splinetool/react-spline';
import { Button } from "@/components/ui/button";
import { ArrowRight, Bot, Cpu, Shield, Zap } from "lucide-react";

const Landing = () => {
    const navigate = useNavigate();

    return (
        <div className="relative min-h-screen w-full overflow-hidden bg-[#0A0010] text-white selection:bg-purple-500/30">
            {/* Background Mesh Gradient */}
            <div className="absolute inset-0 z-0 opacity-60">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-purple-900/40 rounded-full blur-[120px] animate-pulse" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-pink-900/30 rounded-full blur-[120px] animate-pulse" />
                <div className="absolute top-[20%] right-[10%] w-[35%] h-[35%] bg-blue-900/20 rounded-full blur-[100px]" />
                <div className="absolute top-[40%] left-[20%] w-[25%] h-[25%] bg-pink-600/10 rounded-full blur-[80px]" />
            </div>

            {/* Navigation Bar */}
            <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 backdrop-blur-md bg-black/10 border-b border-white/5">
                <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-pink-600 to-purple-600 flex items-center justify-center shadow-[0_0_15px_rgba(236,72,153,0.4)]">
                        <Bot className="h-5 w-5 text-white" />
                    </div>
                    <span className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-pink-100 to-gray-400 font-mono italic">
                        CIF-AI
                    </span>
                </div>
                <div className="hidden md:flex items-center gap-8">
                    <a href="#features" className="text-sm font-medium text-gray-400 hover:text-pink-400 transition-colors">Features</a>
                    <a href="#about" className="text-sm font-medium text-gray-400 hover:text-pink-400 transition-colors">Technology</a>
                </div>
                <div className="flex items-center gap-4">
                    <Button
                        variant="ghost"
                        className="text-white hover:bg-white/10"
                        onClick={() => navigate("/login")}
                    >
                        Login
                    </Button>
                    {/* Nav Get Started removed for cleaner UI */}
                </div>
            </nav>

            {/* Main Split Section */}
            <main className="relative z-10 flex flex-col md:flex-row items-center justify-between min-h-screen w-full max-w-7xl mx-auto px-6 pt-20">

                {/* Left Content (Text) */}
                <div className="w-full md:w-[45%] space-y-8 animate-fade-in py-12 md:py-0">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-pink-500/5 border border-pink-500/20 backdrop-blur-sm">
                        <span className="flex h-2 w-2 rounded-full bg-pink-500 animate-pulse shadow-[0_0_8px_rgba(236,72,153,0.8)]" />
                        <span className="text-xs font-semibold text-pink-200 tracking-[0.2em] uppercase font-mono">Neural Nexus v2.0</span>
                    </div>

                    <h1 className="text-5xl md:text-7xl lg:text-8xl font-black leading-[1.05] tracking-tighter">
                        Meet The <br />
                        <span className="bg-clip-text text-transparent bg-gradient-to-r from-pink-500 via-purple-500 to-blue-400 animate-gradient-x">
                            Future
                        </span>
                    </h1>

                    <p className="text-lg text-gray-300/80 leading-relaxed max-w-lg font-medium">
                        Your AI-powered robotic assistant built for tomorrow. Orchestrating workflows, managing knowledge, and scaling your potential with zero friction.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 pt-4">
                        <Button
                            size="lg"
                            className="group bg-gradient-to-r from-pink-600 to-purple-600 text-white hover:opacity-90 transition-all px-10 h-16 text-xl rounded-2xl shadow-[0_0_30px_rgba(236,72,153,0.4)] border border-pink-400/20"
                            onClick={() => navigate("/signup")}
                        >
                            Get Started
                            <ArrowRight className="ml-2 h-6 w-6 group-hover:translate-x-1 transition-transform" />
                        </Button>
                        <Button
                            size="lg"
                            variant="outline"
                            className="bg-white/5 border-white/10 text-white hover:bg-white/10 px-8 h-16 text-lg rounded-2xl backdrop-blur-md"
                        >
                            Watch Demo
                        </Button>
                    </div>

                    {/* Micro-Features Grid */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 pt-12">
                        <div className="space-y-3 p-4 rounded-2xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-colors group">
                            <Cpu className="h-6 w-6 text-pink-400 group-hover:scale-110 transition-transform" />
                            <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-gray-500">Fast</h3>
                        </div>
                        <div className="space-y-3 p-4 rounded-2xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-colors group">
                            <Shield className="h-6 w-6 text-purple-400 group-hover:scale-110 transition-transform" />
                            <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-gray-500">Secure</h3>
                        </div>
                        <div className="space-y-3 p-4 rounded-2xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-colors group">
                            <Zap className="h-6 w-6 text-blue-400 group-hover:scale-110 transition-transform" />
                            <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-gray-500">Adaptive</h3>
                        </div>
                        <div className="space-y-3 p-4 rounded-2xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] transition-colors group">
                            <Bot className="h-6 w-6 text-pink-500 group-hover:scale-110 transition-transform" />
                            <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-gray-500">Agentic</h3>
                        </div>
                    </div>
                </div>

                {/* Right Content (3D Robot) */}
                <div className="w-full md:w-[55%] h-[50vh] md:h-[85vh] relative group lg:-mr-12">
                    <Spline
                        scene="https://prod.spline.design/UXkPKix99uYO2RxV/scene.splinecode"
                        className="h-full w-full"
                    />
                    {/* Massive glow behind the robot to blend with the pinkish hue */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/3 w-[140%] h-[140%] bg-gradient-to-br from-pink-500/20 via-purple-600/20 to-transparent rounded-full blur-[140px] pointer-events-none -z-10 animate-pulse" />
                </div>
            </main>
        </div>
    );
};

export default Landing;
