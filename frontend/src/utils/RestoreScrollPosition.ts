import { type RefObject, useEffect, useRef } from 'react';

export const useRestoreScrollPosition = (
  key: string,
  restoreReady: boolean,
  scrollRef?: RefObject<HTMLElement | null>
) => {
  const restoringRef = useRef(false);
  const restoredRef = useRef(false);

  const setScrollTop = (top: number) => {
    const target = scrollRef?.current ?? window;

    if (target instanceof Window) {
      target.scrollTo(0, top);
    } else {
      target.scrollTop = top;
    }
  };

  useEffect(() => {
    const target = scrollRef ? scrollRef.current : window;

    if (!target) return;

    const saveScroll = () => {
      if (restoringRef.current) return;

      const top = target instanceof Window ? window.scrollY : target.scrollTop;

      if (top === 0) return;

      sessionStorage.setItem(key, String(top));
    };

    target.addEventListener('scroll', saveScroll);

    return () => {
      target.removeEventListener('scroll', saveScroll);
    };
  }, [key, scrollRef, restoreReady]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState !== 'visible') return;

      const savedY = sessionStorage.getItem(key);
      if (!savedY) return;

      const top = Number(savedY);
      if (top <= 0) return;

      setScrollTop(top);
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [key, scrollRef]);

  useEffect(() => {
    const handleBeforeUnload = () => {
      sessionStorage.setItem(key, '0');
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [key]);

  useEffect(() => {
    if (!restoreReady) return;
    if (restoredRef.current) return;

    const savedY = sessionStorage.getItem(key);
    if (!savedY) return;

    const top = Number(savedY);
    if (top <= 0) return;

    restoringRef.current = true;

    const restore = () => {
      setScrollTop(top);
    };

    restore();
    requestAnimationFrame(restore);

    setTimeout(restore, 100);
    setTimeout(restore, 300);
    setTimeout(restore, 600);

    setTimeout(() => {
      restoringRef.current = false;
      restoredRef.current = true;
    }, 800);
  }, [key, restoreReady, scrollRef]);
};
