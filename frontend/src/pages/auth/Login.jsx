import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import { requestOtp } from "../../services/api";


function Login() {

    const navigate = useNavigate();
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

    const [otpEmail, setOtpEmail] = useState("");
    const [otpCode, setOtpCode] = useState("");
    const [otpSent, setOtpSent] = useState(false);
    const [otpSending, setOtpSending] = useState(false);
    const [otpInfo, setOtpInfo] = useState("");


    useEffect(() => {

        if (user) {
            navigate("/", { replace: true });
        }
    }, [user, navigate]);


    const switchMode = (nextMode) => {

        setMode(nextMode);
        setError("");
        setOtpInfo("");
        setOtpSent(false);
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


    const handleSendOtp = async (event) => {

        event.preventDefault();

        setError("");
        setOtpInfo("");
        setOtpSending(true);

        try {

            await requestOtp(otpEmail);

            setOtpSent(true);
            setOtpInfo(`If ${otpEmail} has an account, a login code was sent to it.`);
        } catch (error) {

            setError(
                error.message ||
                "Could not send a login code. Try again."
            );
        } finally {
            setOtpSending(false);
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
                "That code is invalid or has expired."
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
                            Sign in as <span className="font-semibold text-white">admin</span>, <span className="font-semibold text-white">manager</span>, or <span className="font-semibold text-white">employee</span> to explore the app.
                        </p>
                    </div>

                    <div className="mt-10 grid gap-3 sm:grid-cols-3">
                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Login</p>
                            <p className="mt-2 text-sm text-white">Use alias or email</p>
                        </div>
                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Password</p>
                            <p className="mt-2 text-sm text-white">password</p>
                        </div>
                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Roles</p>
                            <p className="mt-2 text-sm text-white">Admin, Manager, Employee</p>
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

                        <div className="mt-6 inline-flex rounded-2xl bg-slate-100 p-1 text-sm font-medium">
                            <button
                                type="button"
                                onClick={() => switchMode("password")}
                                className={`rounded-xl px-4 py-2 transition ${
                                    mode === "password"
                                        ? "bg-white text-slate-900 shadow"
                                        : "text-slate-500 hover:text-slate-700"
                                }`}
                            >
                                Password
                            </button>

                            <button
                                type="button"
                                onClick={() => switchMode("otp")}
                                className={`rounded-xl px-4 py-2 transition ${
                                    mode === "otp"
                                        ? "bg-white text-slate-900 shadow"
                                        : "text-slate-500 hover:text-slate-700"
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

                        {otpInfo ? (
                            <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
                                {otpInfo}
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
                        ) : (
                            <form
                                onSubmit={otpSent ? handleVerifyOtp : handleSendOtp}
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
                                        disabled={otpSent}
                                        className="mt-2 block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 disabled:bg-slate-50 disabled:text-slate-500"
                                        placeholder="employee@example.com"
                                        required
                                    />
                                </div>

                                {otpSent ? (
                                    <div>
                                        <label
                                            htmlFor="otp-code"
                                            className="block text-sm font-medium text-slate-700"
                                        >
                                            6-digit code
                                        </label>

                                        <input
                                            id="otp-code"
                                            type="text"
                                            inputMode="numeric"
                                            pattern="[0-9]{6}"
                                            maxLength={6}
                                            value={otpCode}
                                            onChange={(event) => setOtpCode(event.target.value.replace(/\D/g, ""))}
                                            className="mt-2 block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-center text-lg tracking-[0.4em] text-slate-900 shadow-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
                                            placeholder="••••••"
                                            required
                                            autoFocus
                                        />

                                        <button
                                            type="button"
                                            onClick={handleSendOtp}
                                            disabled={otpSending}
                                            className="mt-3 text-sm font-medium text-indigo-600 hover:text-indigo-700 disabled:text-slate-400"
                                        >
                                            {otpSending ? "Resending..." : "Resend code"}
                                        </button>
                                    </div>
                                ) : null}

                                <button
                                    type="submit"
                                    disabled={otpSent ? loading : otpSending}
                                    className="w-full rounded-2xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-200 transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                                >
                                    {otpSent
                                        ? (loading ? "Verifying..." : "Verify & sign in")
                                        : (otpSending ? "Sending code..." : "Send login code")}
                                </button>
                            </form>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}


export default Login;