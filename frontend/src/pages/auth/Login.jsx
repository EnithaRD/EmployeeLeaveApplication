import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import { requestOtp } from "../../services/api";


function Login() {

    const navigate = useNavigate();
    const location = useLocation();
    const signupSuccess = Boolean(location.state?.signupSuccess);

    const {
        user,
        login,
        loginWithOtp,
    } = useAuth();

    const [mode, setMode] = useState("password");

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const [otpStep, setOtpStep] = useState("email");
    const [otpEmail, setOtpEmail] = useState("");
    const [otpCode, setOtpCode] = useState("");


    useEffect(() => {

        if (user) {
            navigate("/", { replace: true });
        }
    }, [user, navigate]);


    const switchMode = (nextMode) => {

        setMode(nextMode);
        setError("");
        setOtpStep("email");
        setOtpCode("");
    };


    const handleSubmit = async (event) => {

        event.preventDefault();

        setError("");
        setLoading(true);


        try {

            await login(email, password);

            navigate("/", { replace: true });
        } catch (error) {

            setError(
                error.message ||
                "Invalid email or password"
            );
        } finally {
            setLoading(false);
        }
    };


    const handleRequestOtp = async (event) => {

        event.preventDefault();

        setError("");
        setLoading(true);

        try {

            await requestOtp(otpEmail);

            setOtpStep("code");
        } catch (error) {

            setError(
                error.message ||
                "Could not send the code. Please try again."
            );
        } finally {
            setLoading(false);
        }
    };


    const handleVerifyOtp = async (event) => {

        event.preventDefault();

        setError("");
        setLoading(true);

        try {

            await loginWithOtp(otpEmail, otpCode);

            navigate("/", { replace: true });
        } catch (error) {

            setError(
                error.message ||
                "Invalid or expired code"
            );
        } finally {
            setLoading(false);
        }
    };


    return (
        <div className="min-h-screen bg-[radial-gradient(circle_at_top,#e0e7ff,#f8fafc_45%,#f8fafc)] px-4 py-12">
            <div className="mx-auto grid w-full max-w-5xl gap-8 lg:grid-cols-[1.15fr_0.85fr]">
                <div className="flex flex-col justify-between rounded-4xl bg-slate-950 p-8 text-white shadow-2xl shadow-slate-300 lg:p-10">
                    <div>
                        <div className="inline-flex rounded-full border border-white/15 bg-white/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-indigo-100">
                            Employee Leave Management
                        </div>
                        <h1 className="mt-6 max-w-xl text-4xl font-semibold leading-tight lg:text-5xl">
                            Fast, role-based leave tracking for the whole team.
                        </h1>
                        <p className="mt-4 max-w-xl text-sm leading-6 text-slate-300 lg:text-base">
                            Sign in as <span className="font-semibold text-white">admin</span>, <span className="font-semibold text-white">manager</span>, <span className="font-semibold text-white">HR</span>, or <span className="font-semibold text-white">employee</span> to explore the app.
                        </p>
                    </div>

                    <div className="mt-10 grid gap-3 sm:grid-cols-2">
                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Login</p>
                            <p className="mt-2 text-sm text-white">Use alias or email</p>
                        </div>
                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Roles</p>
                            <p className="mt-2 text-sm text-white">Admin, Manager, HR, Employee</p>
                        </div>
                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Admin / Manager / Employee</p>
                            <p className="mt-2 text-sm text-white">alias + password <span className="font-mono">password</span></p>
                        </div>
                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">HR</p>
                            <p className="mt-2 text-sm text-white break-all">hr@gmail.com / <span className="font-mono">asdfg</span></p>
                        </div>
                    </div>
                </div>

                <div className="flex items-center">
                    <div className="w-full rounded-4xl border border-slate-200 bg-white p-8 shadow-xl shadow-indigo-100/50 lg:p-10">
                        <h2 className="text-3xl font-semibold text-slate-900">
                            Welcome back
                        </h2>

                        <p className="mt-2 text-sm text-slate-600">
                            Login to your account
                        </p>

                        {signupSuccess ? (
                            <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
                                Account created — sign in below.
                            </div>
                        ) : null}

                        <div className="mt-6 inline-flex rounded-full border border-slate-200 bg-slate-100 p-1">
                            <button
                                type="button"
                                onClick={() => switchMode("password")}
                                className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                                    mode === "password"
                                        ? "bg-indigo-600 text-white shadow-sm"
                                        : "text-slate-600 hover:bg-slate-200"
                                }`}
                            >
                                Password
                            </button>
                            <button
                                type="button"
                                onClick={() => switchMode("otp")}
                                className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                                    mode === "otp"
                                        ? "bg-indigo-600 text-white shadow-sm"
                                        : "text-slate-600 hover:bg-slate-200"
                                }`}
                            >
                                Email code
                            </button>
                        </div>

                        {error ? (
                            <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
                                {error}
                            </div>
                        ) : null}

                        {mode === "password" ? (
                            <form
                                onSubmit={handleSubmit}
                                className="mt-8 space-y-6"
                            >
                                <div>
                                    <label
                                        htmlFor="email"
                                        className="block text-sm font-medium text-slate-700"
                                    >
                                        Username or email
                                    </label>

                                    <input
                                        id="email"
                                        type="text"
                                        value={email}
                                        onChange={(event) => setEmail(event.target.value)}
                                        className="mt-2 block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
                                        placeholder="admin"
                                        required
                                    />
                                </div>

                                <div>
                                    <label
                                        htmlFor="password"
                                        className="block text-sm font-medium text-slate-700"
                                    >
                                        Password
                                    </label>

                                    <input
                                        id="password"
                                        type="password"
                                        value={password}
                                        onChange={(event) => setPassword(event.target.value)}
                                        className="mt-2 block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
                                        placeholder="password"
                                        required
                                    />
                                </div>

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full rounded-2xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-200 transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                                >
                                    {loading ? "Signing in..." : "Sign In"}
                                </button>
                            </form>
                        ) : otpStep === "email" ? (
                            <form
                                onSubmit={handleRequestOtp}
                                className="mt-8 space-y-6"
                            >
                                <div>
                                    <label
                                        htmlFor="otp-email"
                                        className="block text-sm font-medium text-slate-700"
                                    >
                                        Email
                                    </label>

                                    <input
                                        id="otp-email"
                                        type="email"
                                        value={otpEmail}
                                        onChange={(event) => setOtpEmail(event.target.value)}
                                        className="mt-2 block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
                                        placeholder="employee@example.com"
                                        required
                                    />
                                </div>

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full rounded-2xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-200 transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                                >
                                    {loading ? "Sending..." : "Send code"}
                                </button>
                            </form>
                        ) : (
                            <form
                                onSubmit={handleVerifyOtp}
                                className="mt-8 space-y-6"
                            >
                                <div>
                                    <p className="text-sm text-slate-600">
                                        Code sent to <span className="font-semibold text-slate-900">{otpEmail}</span>.{" "}
                                        <button
                                            type="button"
                                            onClick={() => setOtpStep("email")}
                                            className="font-semibold text-indigo-600 hover:text-indigo-700"
                                        >
                                            Change email
                                        </button>
                                    </p>
                                </div>

                                <div>
                                    <label
                                        htmlFor="otp-code"
                                        className="block text-sm font-medium text-slate-700"
                                    >
                                        Verification code
                                    </label>

                                    <input
                                        id="otp-code"
                                        type="text"
                                        inputMode="numeric"
                                        maxLength={6}
                                        value={otpCode}
                                        onChange={(event) => setOtpCode(event.target.value)}
                                        className="mt-2 block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
                                        placeholder="123456"
                                        required
                                    />
                                </div>

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full rounded-2xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-200 transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                                >
                                    {loading ? "Verifying..." : "Verify & sign in"}
                                </button>

                                <button
                                    type="button"
                                    onClick={handleRequestOtp}
                                    disabled={loading}
                                    className="w-full text-center text-sm font-semibold text-indigo-600 hover:text-indigo-700 disabled:cursor-not-allowed disabled:text-slate-400"
                                >
                                    Resend code
                                </button>
                            </form>
                        )}

                        <p className="mt-8 text-center text-sm text-slate-600">
                            New here?{" "}
                            <Link
                                to="/signup"
                                className="font-semibold text-indigo-600 hover:text-indigo-700"
                            >
                                Create an account
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}


export default Login;