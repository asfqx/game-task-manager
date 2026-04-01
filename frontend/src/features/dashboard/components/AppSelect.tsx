import { useEffect, useMemo, useRef, useState } from 'react';

type SelectOption = {
  value: string;
  label: string;
};

type AppSelectProps = {
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
};

export function AppSelect({
  value,
  options,
  onChange,
  placeholder = 'Выберите значение',
  disabled = false,
}: AppSelectProps) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const selectedOption = useMemo(
    () => options.find((option) => option.value === value) ?? null,
    [options, value],
  );

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    }

    window.addEventListener('mousedown', handlePointerDown);
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('mousedown', handlePointerDown);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  return (
    <div
      ref={rootRef}
      className={`app-select${isOpen ? ' is-open' : ''}${disabled ? ' is-disabled' : ''}`}
    >
      <button
        type="button"
        className={`app-select__trigger${selectedOption ? '' : ' is-placeholder'}`}
        onClick={() => {
          if (!disabled) {
            setIsOpen((current) => !current);
          }
        }}
        aria-expanded={isOpen}
        disabled={disabled}
      >
        <span>{selectedOption?.label ?? placeholder}</span>
        <span className="app-select__chevron" aria-hidden="true">
          <svg viewBox="0 0 14 14" focusable="false">
            <path d="M3 5.25 7 9.25l4-4" />
          </svg>
        </span>
      </button>

      {isOpen ? (
        <div className="app-select__menu" role="listbox">
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`app-select__option${option.value === value ? ' is-selected' : ''}`}
              onClick={() => {
                onChange(option.value);
                setIsOpen(false);
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
