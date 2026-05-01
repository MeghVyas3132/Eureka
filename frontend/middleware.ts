import { NextRequest, NextResponse } from "next/server";

const AUTH_COOKIE_NAME = "eureka_access_token";

function isProtectedPath(pathname: string): boolean {
  return (
    pathname.startsWith("/dashboard") ||
    pathname.startsWith("/admin") ||
    pathname.startsWith("/super-admin") ||
    pathname.startsWith("/store") ||
    pathname.startsWith("/products")
  );
}

function isAuthPath(pathname: string): boolean {
  return pathname === "/login" || pathname === "/register";
}

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;

  if (isProtectedPath(pathname) && !token) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  if (isAuthPath(pathname) && token) {
    const dashboardUrl = new URL("/dashboard", request.url);
    return NextResponse.redirect(dashboardUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/admin/:path*",
    "/super-admin/:path*",
    "/store/:path*",
    "/products/:path*",
    "/login",
    "/register",
  ],
};
