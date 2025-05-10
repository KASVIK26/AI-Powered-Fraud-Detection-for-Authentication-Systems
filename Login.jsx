import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Login.css';

class BiometricCollector {
  constructor() {
    this.reset();
  }

  reset() {
    this.mouseMovements = [];
    this.keystrokeTimings = [];
    this.lastKeyDown = null;
    this.startTime = Date.now();
  }

  startTracking() {
    this.reset();
    window.addEventListener('mousemove', this.trackMouse);
    window.addEventListener('keydown', this.trackKeyDown);
    window.addEventListener('keyup', this.trackKeyUp);
  }

  trackMouse = (e) => {
    this.mouseMovements.push({
      x: e.clientX,
      y: e.clientY,
      t: Date.now() - this.startTime,
      pageX: e.pageX,
      pageY: e.pageY
    });
  };

  trackKeyDown = (e) => {
    // Ensure e.key is defined and valid
    if (!e.key || e.key.length > 1 || e.repeat) return;
  
    this.lastKeyDown = {
      time: Date.now(),
      key: e.key,
      code: e.code
    };
  };

  trackKeyUp = (e) => {
    if (!this.lastKeyDown || e.key !== this.lastKeyDown.key) return;
    
    this.keystrokeTimings.push({
      key: e.key,
      dwellTime: Date.now() - this.lastKeyDown.time,
      flightTime: this.keystrokeTimings.length > 0 ? 
                 Date.now() - this.keystrokeTimings[this.keystrokeTimings.length - 1].t : 0
    });
  };

  getBiometrics() {
    // Calculate mouse metrics
    const mouseMetrics = {
      movementCount: this.mouseMovements.length,
      avgVelocity: 0,
      movementPattern: []
    };

    if (this.mouseMovements.length > 1) {
      let totalDistance = 0;
      let velocities = [];
      
      for (let i = 1; i < this.mouseMovements.length; i++) {
        const dx = this.mouseMovements[i].x - this.mouseMovements[i-1].x;
        const dy = this.mouseMovements[i].y - this.mouseMovements[i-1].y;
        const dt = (this.mouseMovements[i].t - this.mouseMovements[i-1].t) / 1000;
        
        const distance = Math.sqrt(dx*dx + dy*dy);
        totalDistance += distance;
        
        if (dt > 0) {
          velocities.push(distance / dt);
        }

        mouseMetrics.movementPattern.push({
          dx,
          dy,
          dt,
          v: dt > 0 ? distance / dt : 0
        });
      }

      mouseMetrics.avgVelocity = velocities.length > 0 ? 
        velocities.reduce((a, b) => a + b, 0) / velocities.length : 0;
      mouseMetrics.totalDistance = totalDistance;
    }

    // Calculate keyboard metrics
    const keyboardMetrics = {
      keystrokeCount: this.keystrokeTimings.length,
      avgDwellTime: 0,
      avgFlightTime: 0,
      keyPattern: this.keystrokeTimings.map(ks => ks.key)
    };

    if (this.keystrokeTimings.length > 0) {
      keyboardMetrics.avgDwellTime = this.keystrokeTimings.reduce(
        (sum, ks) => sum + ks.dwellTime, 0) / this.keystrokeTimings.length;
      
      const flightTimes = this.keystrokeTimings.slice(1).map((ks, i) => 
        ks.t - this.keystrokeTimings[i].t);
      
      if (flightTimes.length > 0) {
        keyboardMetrics.avgFlightTime = flightTimes.reduce(
          (sum, ft) => sum + ft, 0) / flightTimes.length;
      }
    }

    return {
      sessionDuration: Date.now() - this.startTime,
      mouse: mouseMetrics,
      keyboard: keyboardMetrics,
      userAgent: navigator.userAgent,
      screenResolution: `${window.screen.width}x${window.screen.height}`,
      collectedAt: new Date().toISOString()
    };
  }

  stopTracking() {
    window.removeEventListener('mousemove', this.trackMouse);
    window.removeEventListener('keydown', this.trackKeyDown);
    window.removeEventListener('keyup', this.trackKeyUp);
  }
}

export default function Login({ setIsAuthenticated }) {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const biometricCollector = useRef(new BiometricCollector());

  useEffect(() => {
    biometricCollector.current.startTracking();
    return () => biometricCollector.current.stopTracking();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const biometrics = biometricCollector.current.getBiometrics();
      
      const response = await axios.post('http://localhost:5000/login', {
        username: credentials.username,
        password: credentials.password,
        biometrics
      }, {
        validateStatus: (status) => status < 500
      });

      if (response.data.success) {
        localStorage.setItem('token', response.data.token);
        localStorage.setItem('username', credentials.username);
        setIsAuthenticated(true);
        navigate('/dashboard');
      } else {
        setError(response.data.message || 'Authentication failed');
        biometricCollector.current.reset();
      }
    } catch (err) {
      setError('Network error. Please try again.');
      console.error('Login error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <img src="./logo.svg" alt="Company Logo" className="logo" />
          <h2>Secure Authentication Portal</h2>
        </div>

        {error && (
          <div className="error-message">
            <i className="fas fa-exclamation-circle"></i>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="username">
              <i className="fas fa-user"></i> Username
            </label>
            <input
              id="username"
              name="username"
              type="text"
              value={credentials.username}
              onChange={handleChange}
              required
              autoComplete="username"
              autoFocus
              disabled={isLoading}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">
              <i className="fas fa-lock"></i> Password
            </label>
            <div className="password-input">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                value={credentials.password}
                onChange={handleChange}
                required
                autoComplete="current-password"
                disabled={isLoading}
              />
              <button 
                type="button" 
                className="toggle-password"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex="-1"
              >
                <i className={`fas ${showPassword ? "fa-eye-slash" : "fa-eye"}`}></i>
              </button>
            </div>
          </div>
          
          <button 
            type="submit" 
            disabled={isLoading || !credentials.username || !credentials.password}
            className={`login-button ${isLoading ? 'loading' : ''}`}
          >
            {isLoading ? (
              <>
                <i className="fas fa-spinner fa-spin"></i> Authenticating...
              </>
            ) : (
              <>
                <i className="fas fa-sign-in-alt"></i> Login
              </>
            )}
          </button>
        </form>

        <div className="login-footer">
          <div className="biometric-notice">
            <i className="fas fa-shield-alt"></i>
            <p>For your security, we analyze behavioral patterns during login</p>
          </div>
          <a href="/forgot-password" className="forgot-password">
            Forgot password?
          </a>
        </div>
      </div>
    </div>
  );
}