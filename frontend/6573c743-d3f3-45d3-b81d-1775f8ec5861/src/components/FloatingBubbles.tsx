import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
interface Bubble {
  id: number;
  size: number;
  x: number;
  y: number;
  delay: number;
  duration: number;
  color: string;
}
export function FloatingBubbles() {
  const bubbles: Bubble[] = useMemo(() => {
    const colors = [
    'rgba(229, 62, 62, 0.6)',
    'rgba(229, 62, 62, 0.3)',
    'rgba(252, 129, 129, 0.4)',
    'rgba(255, 255, 255, 0.15)',
    'rgba(229, 62, 62, 0.8)',
    'rgba(197, 48, 48, 0.5)',
    'rgba(255, 255, 255, 0.08)',
    'rgba(229, 62, 62, 0.45)',
    'rgba(252, 129, 129, 0.25)',
    'rgba(255, 255, 255, 0.12)',
    'rgba(229, 62, 62, 0.55)',
    'rgba(197, 48, 48, 0.35)',
    'rgba(252, 129, 129, 0.5)',
    'rgba(229, 62, 62, 0.2)',
    'rgba(255, 255, 255, 0.1)'];

    return Array.from(
      {
        length: 15
      },
      (_, i) => ({
        id: i,
        size: 30 + Math.random() * 120,
        x: Math.random() * 100,
        y: Math.random() * 100,
        delay: Math.random() * 3,
        duration: 5 + Math.random() * 8,
        color: colors[i % colors.length]
      })
    );
  }, []);
  return (
    <div className="relative w-full h-[400px] md:h-[500px] overflow-hidden rounded-3xl">
      {/* Ambient glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-brand/15 blur-[120px] rounded-full" />

      {bubbles.map((bubble) =>
      <motion.div
        key={bubble.id}
        className="absolute rounded-full"
        style={{
          width: bubble.size,
          height: bubble.size,
          left: `${bubble.x}%`,
          top: `${bubble.y}%`,
          background: `radial-gradient(circle at 30% 30%, ${bubble.color}, transparent 70%)`,
          boxShadow: `inset 0 0 ${bubble.size * 0.3}px ${bubble.color}, 0 0 ${bubble.size * 0.2}px ${bubble.color}`,
          border: `1px solid ${bubble.color.replace(/[\d.]+\)$/, '0.3)')}`,
          backdropFilter: 'blur(2px)'
        }}
        initial={{
          opacity: 0,
          scale: 0.3,
          x: 0,
          y: 0
        }}
        animate={{
          opacity: [0, 1, 1, 0.8, 1],
          scale: [0.3, 1, 1.1, 0.95, 1],
          x: [0, 15, -10, 20, -5, 0],
          y: [0, -20, 10, -15, 5, 0]
        }}
        transition={{
          duration: bubble.duration,
          delay: bubble.delay,
          repeat: Infinity,
          repeatType: 'reverse',
          ease: 'easeInOut'
        }} />

      )}

      {/* Central highlight bubble */}
      <motion.div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-40 rounded-full"
        style={{
          background:
          'radial-gradient(circle at 35% 35%, rgba(229, 62, 62, 0.5), rgba(229, 62, 62, 0.1) 50%, transparent 70%)',
          boxShadow:
          'inset 0 0 60px rgba(229, 62, 62, 0.3), 0 0 80px rgba(229, 62, 62, 0.15)',
          border: '1px solid rgba(229, 62, 62, 0.2)'
        }}
        animate={{
          scale: [1, 1.15, 1],
          opacity: [0.8, 1, 0.8]
        }}
        transition={{
          duration: 6,
          repeat: Infinity,
          ease: 'easeInOut'
        }} />
      

      {/* Specular highlights on some bubbles */}
      {bubbles.slice(0, 6).map((bubble) =>
      <motion.div
        key={`highlight-${bubble.id}`}
        className="absolute rounded-full pointer-events-none"
        style={{
          width: bubble.size * 0.3,
          height: bubble.size * 0.3,
          left: `calc(${bubble.x}% + ${bubble.size * 0.15}px)`,
          top: `calc(${bubble.y}% + ${bubble.size * 0.1}px)`,
          background:
          'radial-gradient(circle, rgba(255,255,255,0.4), transparent 60%)'
        }}
        animate={{
          x: [0, 15, -10, 20, -5, 0],
          y: [0, -20, 10, -15, 5, 0]
        }}
        transition={{
          duration: bubble.duration,
          delay: bubble.delay,
          repeat: Infinity,
          repeatType: 'reverse',
          ease: 'easeInOut'
        }} />

      )}
    </div>);

}