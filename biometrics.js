export class BiometricCollector {
    constructor() {
      this.mouseMovements = [];
      this.keystrokeTimings = [];
      this.lastKeyDown = null;
    }
  
    startTracking() {
      window.addEventListener('mousemove', this.trackMouse);
      window.addEventListener('keydown', this.trackKeyDown);
      window.addEventListener('keyup', this.trackKeyUp);
    }
  
    trackMouse = (e) => {
      this.mouseMovements.push({
        x: e.clientX,
        y: e.clientY,
        t: Date.now()
      });
    };
  
    trackKeyDown = (e) => {
      this.lastKeyDown = Date.now();
    };
  
    trackKeyUp = (e) => {
      if (this.lastKeyDown) {
        this.keystrokeTimings.push({
          key: e.key,
          dwellTime: Date.now() - this.lastKeyDown
        });
      }
    };
  
    getBiometrics() {
      return {
        mouseMovements: this.mouseMovements,
        keystrokeTimings: this.keystrokeTimings
      };
    }
  
    stopTracking() {
      window.removeEventListener('mousemove', this.trackMouse);
      window.removeEventListener('keydown', this.trackKeyDown);
      window.removeEventListener('keyup', this.trackKeyUp);
    }
  }