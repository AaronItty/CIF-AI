import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Bot } from "lucide-react";
import { supabase } from "@/lib/supabase";


const Signup = () => {
  const navigate = useNavigate();
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    console.log("Signup process started...");
    console.log("Email:", email);
    console.log("Company Name:", companyName);

    try {
      console.log("Calling supabase.auth.signUp...");
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            company_name: companyName,
          },
        },
      });

      if (error) {
        console.error("Supabase signup error:", error.message);
        alert(`Signup failed: ${error.message}`);
        return;
      }

      console.log("Supabase signup response data:", data);

      if (data.user) {
        console.log("Signup successful! User ID:", data.user.id);

        // Check if email confirmation is required (session might be null)
        if (!data.session) {
          console.log("Email confirmation required. Please check your inbox.");
          alert("Signup successful! Please check your email to confirm your account.");
        } else {
          console.log("Session established. Navigating to dashboard...");
          navigate("/dashboard");
        }
      } else {
        console.warn("Signup response returned no user data.");
      }
    } catch (err) {
      console.error("Unexpected error during signup:", err);
    } finally {
      setIsLoading(false);
      console.log("Signup process finished.");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary">
            <Bot size={24} className="text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-semibold text-foreground">Create your account</h1>
          <p className="mt-1 text-sm text-muted-foreground">Get started with AgentOS</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Company Name</Label>
            <Input
              placeholder="Acme Corp"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>
          <div className="space-y-2">
            <Label>Email</Label>
            <Input
              type="email"
              placeholder="admin@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>
          <div className="space-y-2">
            <Label>Password</Label>
            <Input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? "Creating Account..." : "Create Account"}
          </Button>
        </form>


        <p className="mt-4 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-primary hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  );
};

export default Signup;
