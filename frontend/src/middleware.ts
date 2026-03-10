import { NextRequest, NextResponse } from "next/server";

const AUTH_COOKIE = "housmart_auth";

const PUBLIC_ROUTES = ["/", "/auth/login", "/auth/signup", "/auth/register"];

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;
    const hasAuth = request.cookies.get(AUTH_COOKIE)?.value === "1";

    const isPublicRoute = PUBLIC_ROUTES.some((path) => pathname === path || pathname.startsWith(`${path}/`));
    const isAuthPage = ["/auth/login", "/auth/signup", "/auth/register"].some(
        (path) => pathname === path || pathname.startsWith(`${path}/`)
    );

    if (!isPublicRoute && !hasAuth) {
        const loginUrl = new URL("/auth/login", request.url);
        return NextResponse.redirect(loginUrl);
    }

    if (isAuthPage && hasAuth) {
        const propertyInputUrl = new URL("/property-input", request.url);
        return NextResponse.redirect(propertyInputUrl);
    }

    return NextResponse.next();
}

export const config = {
    matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
