import { useEffect, useMemo, useRef, useState } from 'react';
import { AppSelect } from './AppSelect';

const WEEKDAY_LABELS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

type DateTimePickerProps = {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
};

type CalendarDay = {
  key: string;
  date: Date;
  isCurrentMonth: boolean;
};

function pad(value: number): string {
  return String(value).padStart(2, '0');
}

function parseLocalDateTime(value: string): Date | null {
  if (!value) return null;

  const match = value.match(
    /^(?<year>\d{4})-(?<month>\d{2})-(?<day>\d{2})T(?<hours>\d{2}):(?<minutes>\d{2})$/,
  );

  if (!match?.groups) return null;

  const { year, month, day, hours, minutes } = match.groups;

  return new Date(
    Number(year),
    Number(month) - 1,
    Number(day),
    Number(hours),
    Number(minutes),
    0,
    0,
  );
}

function toLocalDateTimeValue(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function sameDay(left: Date | null, right: Date): boolean {
  return !!left &&
    left.getFullYear() === right.getFullYear() &&
    left.getMonth() === right.getMonth() &&
    left.getDate() === right.getDate();
}

function startOfCalendar(monthDate: Date): Date {
  const start = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1);
  const offset = (start.getDay() + 6) % 7;
  start.setDate(start.getDate() - offset);
  return start;
}

function buildCalendarDays(monthDate: Date): CalendarDay[] {
  const start = startOfCalendar(monthDate);

  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(start);
    date.setDate(start.getDate() + index);

    return {
      key: `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`,
      date,
      isCurrentMonth: date.getMonth() === monthDate.getMonth(),
    };
  });
}

function buildDateWithTime(date: Date, hours: number, minutes: number): Date {
  return new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate(),
    hours,
    minutes,
    0,
    0,
  );
}

function formatTriggerLabel(date: Date | null, placeholder: string): string {
  if (!date) return placeholder;

  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function DateTimePicker({
  value,
  onChange,
  placeholder = 'Выберите дату и время',
}: DateTimePickerProps) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const selectedDate = parseLocalDateTime(value);
  const [isOpen, setIsOpen] = useState(false);
  const [visibleMonth, setVisibleMonth] = useState<Date>(() => {
    const base = selectedDate ?? new Date();
    return new Date(base.getFullYear(), base.getMonth(), 1);
  });

  useEffect(() => {
    if (!isOpen) return;

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

  useEffect(() => {
    if (!selectedDate) return;

    setVisibleMonth(new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1));
  }, [selectedDate?.getFullYear(), selectedDate?.getMonth()]);

  const calendarDays = useMemo(() => buildCalendarDays(visibleMonth), [visibleMonth]);
  const monthLabel = new Intl.DateTimeFormat('ru-RU', {
    month: 'long',
    year: 'numeric',
  }).format(visibleMonth);

  const effectiveDate = selectedDate ?? new Date();
  const hoursValue = pad(effectiveDate.getHours());
  const minutesValue = pad(effectiveDate.getMinutes());

  function updateDate(nextDate: Date) {
    onChange(toLocalDateTimeValue(nextDate));
  }

  function handleSelectDay(day: Date) {
    updateDate(buildDateWithTime(day, effectiveDate.getHours(), effectiveDate.getMinutes()));
  }

  function handleTimePartChange(part: 'hours' | 'minutes', nextValue: string) {
    const baseDate =
      selectedDate ??
      buildDateWithTime(new Date(), Number(hoursValue), Number(minutesValue));

    const nextDate = buildDateWithTime(
      baseDate,
      part === 'hours' ? Number(nextValue) : baseDate.getHours(),
      part === 'minutes' ? Number(nextValue) : baseDate.getMinutes(),
    );

    updateDate(nextDate);
  }

  function handleToday() {
    const now = new Date();
    const rounded = buildDateWithTime(now, now.getHours(), now.getMinutes());
    updateDate(rounded);
    setVisibleMonth(new Date(rounded.getFullYear(), rounded.getMonth(), 1));
  }

  return (
    <div className={`date-time-picker${isOpen ? ' is-open' : ''}`} ref={rootRef}>
      <button
        type="button"
        className={`date-time-picker__trigger${selectedDate ? '' : ' is-empty'}`}
        onClick={() => setIsOpen((current) => !current)}
        aria-expanded={isOpen}
      >
        <span>{formatTriggerLabel(selectedDate, placeholder)}</span>
        <span className="date-time-picker__trigger-icon" aria-hidden="true">
          <svg viewBox="0 0 20 20" focusable="false">
            <path d="M6 2a1 1 0 0 1 1 1v1h6V3a1 1 0 1 1 2 0v1h1.25A2.75 2.75 0 0 1 19 6.75v9.5A2.75 2.75 0 0 1 16.25 19h-12.5A2.75 2.75 0 0 1 1 16.25v-9.5A2.75 2.75 0 0 1 3.75 4H5V3a1 1 0 0 1 1-1Zm10.25 7h-12.5v7.25c0 .41.34.75.75.75h11c.41 0 .75-.34.75-.75V9Zm-.75-3h-11a.75.75 0 0 0-.75.75V7h12.5v-.25a.75.75 0 0 0-.75-.75Z" />
          </svg>
        </span>
      </button>

      {isOpen ? (
        <div className="date-time-picker__popover">
          <div className="date-time-picker__header">
            <button
              type="button"
              className="date-time-picker__nav"
              onClick={() =>
                setVisibleMonth(
                  (current) => new Date(current.getFullYear(), current.getMonth() - 1, 1),
                )
              }
              aria-label="Предыдущий месяц"
            >
              ‹
            </button>
            <strong>{monthLabel}</strong>
            <button
              type="button"
              className="date-time-picker__nav"
              onClick={() =>
                setVisibleMonth(
                  (current) => new Date(current.getFullYear(), current.getMonth() + 1, 1),
                )
              }
              aria-label="Следующий месяц"
            >
              ›
            </button>
          </div>

          <div className="date-time-picker__weekdays">
            {WEEKDAY_LABELS.map((label) => (
              <span key={label}>{label}</span>
            ))}
          </div>

          <div className="date-time-picker__grid">
            {calendarDays.map((day) => {
              const isSelected = sameDay(selectedDate, day.date);
              const isToday = sameDay(new Date(), day.date);

              return (
                <button
                  key={day.key}
                  type="button"
                  className={[
                    'date-time-picker__day',
                    day.isCurrentMonth ? '' : 'is-outside',
                    isSelected ? 'is-selected' : '',
                    isToday ? 'is-today' : '',
                  ]
                    .filter(Boolean)
                    .join(' ')}
                  onClick={() => handleSelectDay(day.date)}
                >
                  {day.date.getDate()}
                </button>
              );
            })}
          </div>

          <div className="date-time-picker__time">
            <label className="date-time-picker__time-field">
              <span>Часы</span>
              <AppSelect
                value={hoursValue}
                onChange={(value) => handleTimePartChange('hours', value)}
                options={Array.from({ length: 24 }, (_, hour) => {
                  const option = pad(hour);
                  return { value: option, label: option };
                })}
              />
            </label>

            <label className="date-time-picker__time-field">
              <span>Минуты</span>
              <AppSelect
                value={minutesValue}
                onChange={(value) => handleTimePartChange('minutes', value)}
                options={Array.from({ length: 60 }, (_, minute) => {
                  const option = pad(minute);
                  return { value: option, label: option };
                })}
              />
            </label>
          </div>

          <div className="date-time-picker__actions">
            <button type="button" className="ghost-button" onClick={handleToday}>
              Сегодня
            </button>
            <button type="button" className="ghost-button" onClick={() => onChange('')}>
              Очистить
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
