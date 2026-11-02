/** Ícones próprios (traço 1,8 px, grade 24). Decorativos por padrão: aria-hidden. */
import type { SVGProps } from 'react';

const PATHS = {
  cube: 'M12 2.5 20.5 7v10L12 21.5 3.5 17V7z M3.5 7 12 11.5 20.5 7 M12 11.5v10',
  flask: 'M9 3h6 M10 3v6L4.5 19a1.5 1.5 0 0 0 1.3 2.2h12.4A1.5 1.5 0 0 0 19.5 19L14 9V3 M7.5 14h9',
  book: 'M4 4.5A1.5 1.5 0 0 1 5.5 3H20v15H5.5A1.5 1.5 0 0 0 4 19.5z M4 19.5A1.5 1.5 0 0 0 5.5 21H20 M8 7h8',
  teacher: 'M3 4h18v11H3z M8 21l4-6 4 6 M7 8h6 M7 11h4',
  notebook: 'M6 3h12a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H6z M6 3v18 M9 8h7 M9 12h7 M3.5 7h3 M3.5 12h3 M3.5 17h3',
  command: 'M9 6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3z',
  settings: 'M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z',
  sun: 'M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M12 2v2 M12 20v2 M4.9 4.9l1.4 1.4 M17.7 17.7l1.4 1.4 M2 12h2 M20 12h2 M4.9 19.1l1.4-1.4 M17.7 6.3l1.4-1.4',
  moon: 'M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11z',
  undo: 'M9 14 4 9l5-5 M4 9h10.5a5.5 5.5 0 0 1 0 11H11',
  redo: 'M15 14l5-5-5-5 M20 9H9.5a5.5 5.5 0 0 0 0 11H13',
  share: 'M18 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M6 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M18 22a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M8.6 13.5l6.8 4 M15.4 6.5l-6.8 4',
  download: 'M12 3v12 M7 10l5 5 5-5 M5 21h14',
  upload: 'M12 21V9 M7 14l5-5 5 5 M5 3h14',
  play: 'M7 4.5v15l12-7.5z',
  pause: 'M7 4h3.5v16H7z M13.5 4H17v16h-3.5z',
  restart: 'M3 12a9 9 0 1 0 3-6.7L3 8 M3 3v5h5',
  step: 'M5 5l9 7-9 7z M17 5v14',
  stepBack: 'M19 5l-9 7 9 7z M7 5v14',
  close: 'M6 6l12 12 M18 6 6 18',
  check: 'M4.5 12.5l5 5 10-11',
  alert: 'M12 3 2.5 20h19z M12 10v4.5 M12 17.5v.5',
  info: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M12 11v5.5 M12 7.5v.5',
  eye: 'M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
  eyeOff: 'M3 3l18 18 M10.6 5.1A10 10 0 0 1 12 5c6.4 0 10 7 10 7a17.6 17.6 0 0 1-3.2 4.1 M6.6 6.6A17.4 17.4 0 0 0 2 12s3.6 7 10 7a9.6 9.6 0 0 0 5.4-1.6 M9.9 9.9a3 3 0 0 0 4.2 4.2',
  trash: 'M4 7h16 M9 7V4h6v3 M6 7l1 14h10l1-14 M10 11v6 M14 11v6',
  ruler: 'M3 17 17 3l4 4L7 21z M7 13l2 2 M10 10l2 2 M13 7l2 2',
  angle: 'M4 20h16 M4 20 16 5 M10 20a6 6 0 0 0-2-4.5',
  target: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M12 12.5v-1',
  layers: 'M12 3 2 8.5l10 5.5 10-5.5z M2 15l10 5.5L22 15 M2 11.7l10 5.5 10-5.5',
  grid: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
  wifi: 'M2 8.5a15 15 0 0 1 20 0 M5.5 12a10 10 0 0 1 13 0 M9 15.5a5 5 0 0 1 6 0 M12 19.5v.5',
  wifiOff: 'M3 3l18 18 M8.5 15.5a5 5 0 0 1 5.6-.6 M5.5 12a10 10 0 0 1 3.4-2 M2 8.5A15 15 0 0 1 6 6.1 M12 19.5v.5 M14.8 9.4A10 10 0 0 1 18.5 12 M17.6 5.6A15 15 0 0 1 22 8.5',
  server: 'M4 4h16v6H4z M4 14h16v6H4z M7.5 7h.5 M7.5 17h.5',
  lock: 'M6 11h12v10H6z M8.5 11V7.5a3.5 3.5 0 0 1 7 0V11',
  unlock: 'M6 11h12v10H6z M8.5 11V7.5a3.5 3.5 0 0 1 6.8-1.2',
  plus: 'M12 5v14 M5 12h14',
  minus: 'M5 12h14',
  search: 'M10.5 18a7.5 7.5 0 1 0 0-15 7.5 7.5 0 0 0 0 15z M16 16l5 5',
  chevronDown: 'M6 9l6 6 6-6',
  chevronRight: 'M9 6l6 6-6 6',
  pencil: 'M4 20l1-4L16.5 4.5a2.1 2.1 0 0 1 3 3L8 19z M14.5 6.5l3 3',
  calc: 'M5 3h14v18H5z M8 7h8 M8 11h2 M14 11h2 M8 15h2 M14 15h2 M8 18.5h2 M14 18.5h2',
  bulb: 'M9 18h6 M10 21h4 M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2V16h5v-.1c0-.8.4-1.5 1-2A6 6 0 0 0 12 3z',
  demo: 'M4 4h16v16H4z M4 9.5 9.5 4 M4 15l11-11 M4 20.5 20.5 4 M9.5 20 20 9.5 M15 20l5-5',
  camera: 'M3 8h3.5L8 5.5h8L17.5 8H21v11H3z M12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
  print: 'M6 9V3h12v6 M6 18H3.5V9h17v9H18 M6 14h12v7H6z',
  sparkles: 'M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z M19 15l.8 2.2 2.2.8-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z',
  link: 'M10 14a4.5 4.5 0 0 0 6.4 0l3-3a4.5 4.5 0 0 0-6.4-6.4l-1 1 M14 10a4.5 4.5 0 0 0-6.4 0l-3 3a4.5 4.5 0 0 0 6.4 6.4l1-1',
  axes: 'M5 19V4 M5 19h15 M5 19l-2.5 2.5 M5 4 3.5 6 M5 4l1.5 2 M20 19l-2-1.5 M20 19l-2 1.5',
  atom: 'M12 13.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z M12 21c-2.5 0-4.5-4-4.5-9S9.5 3 12 3s4.5 4 4.5 9-2 9-4.5 9z M4.2 16.5C3 14.3 5.8 10.5 10.2 8s9-2.7 10.3-.6-1.5 6-5.9 8.5-9.1 2.8-10.4.6z',
  plane: 'M3 16 9 6h12l-6 10z',
  arrowRight: 'M4 12h15 M14 6.5 19.5 12 14 17.5',
  history: 'M3 12a9 9 0 1 0 3-6.7L3 8 M3 3v5h5 M12 7v5l3.5 2',
  question: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M9.5 9.2a2.6 2.6 0 0 1 5 1c0 1.8-2.5 2.2-2.5 3.8 M12 17.4v.4',
  menu: 'M4 6h16 M4 12h16 M4 18h16',
  file: 'M6 3h8.5L19 7.5V21H6z M14 3v5h5',
  terminal: 'M4 4h16v16H4z M7.5 9l3 3-3 3 M12.5 15h4',
  scissors: 'M6 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M8.1 7.9 20 18 M8.1 16.1 20 6',
  stack: 'M5 19h14 M7 15h10 M5 11h14 M7 7h10',
  thermometer: 'M10 13.5V5a2 2 0 1 1 4 0v8.5a4 4 0 1 1-4 0z M12 9v6',
  swap: 'M7 4 3 8l4 4 M3 8h14 M17 12l4 4-4 4 M21 16H7',
} as const;

export type IconName = keyof typeof PATHS;

interface IconProps extends Omit<SVGProps<SVGSVGElement>, 'name'> {
  name: IconName;
  size?: number;
  /** quando informado, o ícone deixa de ser decorativo */
  title?: string;
}

export function Icon({ name, size = 18, title, ...rest }: IconProps) {
  const d = PATHS[name];
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={title ? undefined : true}
      role={title ? 'img' : undefined}
      focusable="false"
      className="ds-icon"
      {...rest}
    >
      {title ? <title>{title}</title> : null}
      {d.split(' M').map((seg, i) => (
        <path key={i} d={i === 0 ? seg : `M${seg}`} />
      ))}
    </svg>
  );
}
