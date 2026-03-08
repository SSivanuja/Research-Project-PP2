import React from 'react';
import { Scale } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LogoProps {
  variant?: 'default' | 'light';
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  className?: string;
}

const Logo = ({ variant = 'default', size = 'md', showText = true, className }: LogoProps) => {
  const sizeClasses = {
    sm: { icon: 'h-5 w-5', text: 'text-lg' },
    md: { icon: 'h-6 w-6', text: 'text-xl' },
    lg: { icon: 'h-8 w-8', text: 'text-2xl' },
  };

  const colorClasses = {
    default: {
      icon: 'text-primary',
      text: 'text-foreground',
    },
    light: {
      icon: 'text-accent',
      text: 'text-primary-foreground',
    },
  };

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className={cn(
        'flex items-center justify-center rounded-lg p-1.5',
        variant === 'light' ? 'bg-primary-foreground/10' : 'bg-primary/10'
      )}>
        <Scale className={cn(sizeClasses[size].icon, colorClasses[variant].icon)} />
      </div>
      {showText && (
        <span className={cn(
          'font-display font-bold tracking-tight',
          sizeClasses[size].text,
          colorClasses[variant].text
        )}>
          Legal Insights Hub
        </span>
      )}
    </div>
  );
};

export default Logo;
