import { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, User, Sparkles, LogIn, UserPlus } from 'lucide-react';
import { authAPI } from '../api/axiosConfig';
import { GoogleLogin } from '@react-oauth/google';

const Login = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let response;
      if (isLogin) {
        response = await authAPI.login(username, password);
      } else {
        response = await authAPI.register(username, password);
      }

      // Store token and username
      localStorage.setItem('access_token', response.access_token);
      // 🔥 NEW: Added your custom neo_auth_token here!
      localStorage.setItem('neo_auth_token', response.access_token);
      localStorage.setItem('username', username);
      
      // Call success callback
      onLoginSuccess();
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        `${isLogin ? 'Login' : 'Registration'} failed. Please try again.`
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-cyber-darker relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute top-20 left-20 w-96 h-96 bg-cyber-purple rounded-full opacity-10 blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            rotate: [0, 90, 0],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute bottom-20 right-20 w-96 h-96 bg-cyber-blue rounded-full opacity-10 blur-3xl"
          animate={{
            scale: [1.2, 1, 1.2],
            rotate: [90, 0, 90],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </div>

      {/* Login Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 w-full max-w-md p-8"
      >
        <div className="glass rounded-2xl p-8 shadow-2xl glow-strong">
          {/* Header */}
          <div className="text-center mb-8">
            <motion.div
              className="inline-block mb-4"
              animate={{
                rotate: [0, 360],
              }}
              transition={{
                duration: 20,
                repeat: Infinity,
                ease: "linear",
              }}
            >
              <Sparkles className="w-16 h-16 text-cyber-purple" />
            </motion.div>
            <h1 className="text-4xl font-bold gradient-text mb-2">
              Neo AI
            </h1>
            <p className="text-slate-400">
              {isLogin ? 'Welcome back' : 'Create your account'}
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username Field */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-cyber-purple" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-cyber-dark border border-cyber-purple/30 rounded-lg 
                               text-white placeholder-slate-500 focus:outline-none focus:border-cyber-purple 
                               focus:ring-2 focus:ring-cyber-purple/20 transition-all"
                  placeholder="Enter username"
                  required
                  minLength={3}
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-cyber-purple" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-cyber-dark border border-cyber-purple/30 rounded-lg 
                               text-white placeholder-slate-500 focus:outline-none focus:border-cyber-purple 
                               focus:ring-2 focus:ring-cyber-purple/20 transition-all"
                  placeholder="Enter password"
                  required
                  minLength={6}
                />
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm"
              >
                {error}
              </motion.div>
            )}

            {/* Submit Button */}
            <motion.button
              type="submit"
              disabled={loading}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full py-3 bg-gradient-to-r from-cyber-purple to-cyber-blue rounded-lg 
                       text-white font-semibold flex items-center justify-center space-x-2
                       hover:shadow-lg hover:shadow-cyber-purple/50 transition-all
                       disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                >
                  <Sparkles className="w-5 h-5" />
                </motion.div>
              ) : (
                <>
                  {isLogin ? <LogIn className="w-5 h-5" /> : <UserPlus className="w-5 h-5" />}
                  <span>{isLogin ? 'Sign In' : 'Sign Up'}</span>
                </>
              )}
            </motion.button>
          </form>

          {/* Toggle Login/Register */}
          <div className="mt-6 text-center">
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
              }}
              className="text-cyber-purple hover:text-cyber-blue transition-colors"
            >
              {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
            </button>
          </div>

          {/* 🔥 GOOGLE LOGIN BUTTON SECTION 🔥 */}
          <div className="mt-6 flex flex-col items-center">
            <div className="flex items-center w-full mb-4">
              <div className="flex-1 border-t border-slate-700"></div>
              <span className="px-3 text-slate-400 text-sm">Or continue with</span>
              <div className="flex-1 border-t border-slate-700"></div>
            </div>
            
           <GoogleLogin
             onSuccess={async (credentialResponse) => {
               try {
                 setLoading(true);
                 setError('');
                 
                 // 1. Send the Google token to your backend
                 const response = await authAPI.googleLogin(credentialResponse.credential);
                 
                 // 2. Store the login data exactly like your normal login does
                 localStorage.setItem('access_token', response.access_token);
                 // 🔥 NEW: Added your custom neo_auth_token here for Google Auth too!
                 localStorage.setItem('neo_auth_token', response.access_token);
                 localStorage.setItem('username', response.username);
                 
                 // 3. BOOM! Open the chat interface!
                 onLoginSuccess();
                 
               } catch (err) {
                 console.error("Backend rejected Google token:", err);
                 setError('Google Authentication failed. Please try again.');
               } finally {
                 setLoading(false);
               }
             }}
             onError={() => {
               console.log('Login Failed');
               setError('Google Login Window Closed or Failed.');
             }}
             theme="filled_black"
             shape="pill"
           />
          </div>

        </div>
      </motion.div>
    </div>
  );
};

export default Login;