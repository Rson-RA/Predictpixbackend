/// <reference types="react-scripts" />

declare namespace JSX {
  interface IntrinsicElements {
    div: React.DetailedHTMLProps<React.HTMLAttributes<HTMLDivElement>, HTMLDivElement>;
  }
}

declare module '@mui/material' {
  export interface Theme {
    palette: {
      primary: {
        main: string;
      };
      secondary: {
        main: string;
      };
      background: {
        default: string;
      };
    };
  }
}
