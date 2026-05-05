import { AlertCircle, UserPlus } from 'lucide-react';
import React, { useState } from 'react';
import { apiService } from '../services/api';

interface RegisterProps {
    onRegisterSuccess: () => void;
    onSwitchToLogin: () => void;
}

export const Register: React.FC<RegisterProps> = ({ onSwitchToLogin }) => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [fullName, setFullName] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    // Inside Register.tsx
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        if (password !== confirmPassword) {
            setError('confirm_password: Passwords do not match');
            return;
        }

        if (password.length < 8) {
            setError('password: Password must be at least 8 characters');
            return;
        }
        setLoading(true);

        try {
            const payload = {
                username: username.toLowerCase().trim(),
                email: email.trim(),
                password: password,
                confirm_password: confirmPassword,
                full_name: fullName.trim(),
                age: 18,      // Using 18 to safely clear the "minimum 13" rule
                tags: ["user"]
            };

            // Log exactly what you are sending to the API
            //console.log("Sending Register Payload:", payload);

            await apiService.register(payload);
            // 1. Optional: Add a success notification or alert here
            alert("Registration successful! Please sign in with your new credentials.");
            // 2. Redirect to the Login view
            onSwitchToLogin();
        } catch (err: any) {
            const responseData = err.response?.data;
            // 1. Check for your specific backend error structure
            if (responseData?.error_code === "VALIDATION_ERROR" && Array.isArray(responseData.errors)) {
                // Extract each field's error message
                const fieldErrors = responseData.errors.map((e: any) =>
                    `${e.field}: ${e.message}`
                );

                // Join them with a line break or bullet point
                setError(fieldErrors.join(' | '));
                console.error("Backend Validation Details:", responseData.errors);
            }
            // 2. Fallback for standard detail errors
            else if (responseData?.detail) {
                setError(typeof responseData.detail === 'string'
                    ? responseData.detail
                    : 'Check your input details.');
            }
            // 3. General network error
            else {
                setError('Registration failed. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center p-4">
            <div className="card w-full max-w-md p-8">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Create Account</h1>
                    <p className="text-gray-600">Sign up to get started with AIVerse</p>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                        <div className="flex items-start gap-2">
                            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                            <div className="text-sm text-red-700">
                                <p className="font-bold mb-1">Validation Issues:</p>
                                <ul className="list-disc ml-4">
                                    {error.split(' | ').map((msg, i) => (
                                        <li key={i}>{msg}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Full Name Field */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                        <input
                            type="text"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            className="input w-full"
                            placeholder="John Doe"
                        />
                        <p className="text-[11px] text-gray-500 mt-1">Letters only, proper capitalization preferred.</p>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Username
                        </label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="input"
                            required
                            autoFocus
                        />
                        <p className="text-[11px] text-gray-500 mt-1">3-50 chars: letters, numbers, underscores, or hyphens.</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Email
                        </label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="input"
                            required
                        />
                        <p className="text-[11px] text-gray-500 mt-1">Must be from: gmail.com, yahoo.com, outlook.com, or example.com.</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Password
                        </label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="input"
                            required
                            minLength={8}
                        />
                        <p className="text-[11px] text-gray-500 mt-1">Min. 8 chars with 1 uppercase, 1 lowercase, and 1 number.</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Confirm Password
                        </label>
                        <input
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className="input"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full btn btn-primary flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <>
                                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                Creating account...
                            </>
                        ) : (
                            <>
                                <UserPlus className="w-5 h-5" />
                                Sign Up
                            </>
                        )}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <p className="text-sm text-gray-600">
                        Already have an account?{' '}
                        <button
                            onClick={onSwitchToLogin}
                            className="text-primary-500 hover:text-primary-600 font-medium"
                        >
                            Sign in
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};