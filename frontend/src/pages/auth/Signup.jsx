import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { signupUser } from "../../services/api";


function Signup() {

    const navigate = useNavigate();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [role, setRole] = useState("EMPLOYEE");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);


    const handleSubmit = async (event) => {

        event.preventDefault();

        setError("");
        setLoading(true);

        try {

            await signupUser({
                email,
                password,
                role,
            });

            navigate("/login", { state: { signupSuccess: true } });
        } catch (error) {

            const status = error.response?.status;

            if (status === 409) {
                setError("An account with this email already exists.");
            } else {
                setError(
                    error.response?.data?.detail ||
                    "Could not create the account. Please try again."
                );
            }
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
                            Create your account and start tracking leave.
                        </h1>
                        <p className="mt-4 max-w-xl text-sm leading-6 text-slate-300 lg:text-base">
                            Sign up as an <span className="font-semibold text-white">employee</span> or a <span className="font-semibold text-white">manager</span> — an admin can assign your department later.
                        </p>
                    </div>

                    <div className="mt-10 grid gap-3 sm:grid-cols-2">
                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Roles</p>
                            <p className="mt-2 text-sm text-white">Employee, Manager</p>
                        </div>
                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Next step</p>
                            <p className="mt-2 text-sm text-white">Sign in after creating your account</p>
                        </div>
                    </div>
                </div>

                <div className="flex items-center">
                    <div className="w-full rounded-4xl border border-slate-200 bg-white p-8 shadow-xl shadow-indigo-100/50 lg:p-10">
                        <h2 className="text-3xl font-semibold text-slate-900">
                            Create your account
                        </h2>

                        <p className="mt-2 text-sm text-slate-600">
                            It only takes a minute
                        </p>

                        {error ? (
                            <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
                                {error}
                            </div>
                        ) : null}

                        <form
                            onSubmit={handleSubmit}
                            className="mt-8 space-y-6"
                        >
                            <div>
                                <label
                                    htmlFor="signup-email"
                                    className="block text-sm font-medium text-slate-700"
                                >
                                    Email
                                </label>

                                <input
                                    id="signup-email"
                                    type="email"
                                    value={email}
                                    onChange={(event) => setEmail(event.target.value)}
                                    className="mt-2 block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
                                    placeholder="jane.doe@example.com"
                                    required
                                />
                            </div>

                            <div>
                                <label
                                    htmlFor="signup-password"
                                    className="block text-sm font-medium text-slate-700"
                                >
                                    Password
                                </label>

                                <input
                                    id="signup-password"
                                    type="password"
                                    value={password}
                                    onChange={(event) => setPassword(event.target.value)}
                                    className="mt-2 block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
                                    placeholder="Choose a password"
                                    required
                                />
                            </div>

                            <div>
                                <label
                                    htmlFor="signup-role"
                                    className="block text-sm font-medium text-slate-700"
                                >
                                    Role
                                </label>

                                <select
                                    id="signup-role"
                                    value={role}
                                    onChange={(event) => setRole(event.target.value)}
                                    className="mt-2 block w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
                                >
                                    <option value="EMPLOYEE">Employee</option>
                                    <option value="MANAGER">Manager</option>
                                </select>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full rounded-2xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-200 transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                            >
                                {loading ? "Creating account..." : "Create account"}
                            </button>
                        </form>

                        <p className="mt-8 text-center text-sm text-slate-600">
                            Already have an account?{" "}
                            <Link
                                to="/login"
                                className="font-semibold text-indigo-600 hover:text-indigo-700"
                            >
                                Sign in
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}


export default Signup;
