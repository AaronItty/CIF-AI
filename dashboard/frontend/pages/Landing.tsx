import { useNavigate } from "react-router-dom";
import Spline from '@splinetool/react-spline';
import { Button } from "@/components/ui/button";
import { ArrowRight, Bot } from "lucide-react";
import GlitchText from "@/components/GlitchText";
import ClickSpark from "@/components/ClickSpark";
import Aurora from "@/components/Aurora";

const Landing = () => {
    const navigate = useNavigate();

    return (
        <ClickSpark
            sparkColor="#ec4899"
            sparkSize={12}
            sparkRadius={20}
            sparkCount={10}
            duration={500}
        >
            <div className="relative min-h-screen w-full overflow-hidden bg-[#0A0010] text-white selection:bg-purple-500/30">
                {/* Style to hide Spline watermark and handle canvas isolation */}
                <style>
                    {`
                    #spline-watermark, 
                    .spline-watermark,
                    a[href*="spline.design"],
                    a[href*="spline"],
                    [class*="spline-watermark"] {
                        display: none !important;
                        opacity: 0 !important;
                        pointer-events: none !important;
                        visibility: hidden !important;
                        width: 0 !important;
                        height: 0 !important;
                    }

                    canvas {
                        outline: none !important;
                    }
                    
                    .spline-container {
                        mask-image: linear-gradient(to left, black 90%, transparent 100%), 
                                    linear-gradient(to top, black 90%, transparent 100%),
                                    linear-gradient(to right, black 90%, transparent 100%);
                        -webkit-mask-image: linear-gradient(to left, black 90%, transparent 100%), 
                                            linear-gradient(to top, black 90%, transparent 100%),
                                            linear-gradient(to right, black 90%, transparent 100%);
                    }
                `}
                </style>

                {/* Background 3D Aurora Effect */}
                <div className="absolute inset-0 z-0 opacity-50">
                    <Aurora
                        colorStops={["#5227FF", "#b045a7", "#711d72"]}
                        amplitude={1}
                        blend={0.5}
                    />
                </div>

                {/* Background Mesh Gradient (Subtle Backup) */}
                <div className="absolute inset-0 z-0 opacity-20">
                    <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-purple-900/40 rounded-full blur-[120px] animate-pulse" />
                    <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-pink-900/20 rounded-full blur-[140px] animate-pulse" />
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
                    </div>
                </nav>

                {/* Main Split Section */}
                <main className="relative z-20 flex flex-col md:flex-row items-center justify-between h-screen w-full max-w-7xl mx-auto px-6 py-20 overflow-hidden">

                    {/* Left Content (Text) */}
                    <div className="w-full md:w-[45%] space-y-8 animate-fade-in flex flex-col justify-center">
                        <h1 className="text-5xl md:text-7xl lg:text-8xl font-black leading-[1.05] tracking-tighter">
                            Meet The <br />
                            <GlitchText
                                speed={2.5}
                                enableShadows
                                enableOnHover={false}
                                className="bg-clip-text text-transparent bg-gradient-to-r from-pink-500 via-purple-500 to-blue-400 inline-block"
                            >
                                Future
                            </GlitchText>
                        </h1>

                        <p className="text-lg text-gray-300/80 leading-relaxed max-w-lg font-medium">
                            Your AI-powered  assistant built for tomorrow. Orchestrating workflows, managing knowledge, and help deal with customer interactions.
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
                    </div>

                    {/* Right Content (3D Robot) */}
                    <div className="w-full md:w-[55%] h-full relative group lg:-mr-12 spline-container">
                        <Spline
                            scene="https://prod.spline.design/UXkPKix99uYO2RxV/scene.splinecode"
                            className="h-full w-full"
                        />

                        {/* Vignette Overlay to blend edges further */}
                        <div className="absolute inset-0 z-30 pointer-events-none bg-[radial-gradient(circle_at_center,transparent_40%,#0A0010_100%)]" />

                        {/* Gradient Blur Overlay (Bottom Right) to hide watermark and blend edges */}
                        <div className="absolute bottom-4 right-4 w-64 h-24 bg-purple-900/10 backdrop-blur-xl [mask-image:linear-gradient(to_top,black_40%,transparent_100%)] z-40 pointer-events-none rounded-3xl border border-white/5" />
                        <div className="absolute bottom-0 right-0 w-full h-32 bg-gradient-to-t from-[#0A0010] via-[#0A0010]/80 to-transparent z-30 pointer-events-none" />

                        {/* Massive glow behind the robot */}
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/3 w-[140%] h-[140%] bg-gradient-to-br from-pink-500/15 via-purple-600/15 to-transparent rounded-full blur-[160px] pointer-events-none -z-10 animate-pulse" />
                    </div>
                </main>
            </div>
        </ClickSpark>
    );
};

export default Landing;
