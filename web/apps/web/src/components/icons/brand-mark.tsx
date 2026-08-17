import type { SVGProps } from "react";

export function BrandMark(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      shapeRendering="crispEdges"
      aria-hidden="true"
      {...props}
    >
      <path d="M2 0h3v2h2v2h2v2h2v2h1v6h-2v3H8v-2H6v-2H4v-2H2V9H1V6H0V3h1V1h1V0Zm13 6h4v1h2v2h2v2h1v2l-7 7-7-7 2-2h1V9h2V6ZM0 16h8l4 4-2 2H8v2H5v-1H3v-2H1v-2H0v-3Zm10 1 3-3 2 2h2v2h2v2h2v2h3v2h-6v-1h-3v-2h-2v-2h-2v-1h-1v-1Z" />
    </svg>
  );
}
