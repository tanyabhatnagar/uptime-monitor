import { useEffect, useRef } from "react";

/**
 * A custom React hook that sets up an interval and clears it when unmounted.
 * It is resilient to changes in the callback function or delay.
 * 
 * @param {Function} callback - The function to run every tick.
 * @param {number|null} delay - The interval delay in milliseconds (pass null to pause).
 */
export function useInterval(callback, delay) {
  const savedCallback = useRef();

  // Remember the latest callback
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // Set up the interval
  useEffect(() => {
    function tick() {
      if (savedCallback.current) {
        savedCallback.current();
      }
    }

    if (delay !== null) {
      const id = setInterval(tick, delay);
      return () => clearInterval(id);
    }
  }, [delay]);
}

export default useInterval;
