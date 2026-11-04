import { Link } from "react-router-dom";

function StatusPage({ code, title, message }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <p className="text-sm font-semibold text-navy-600">{code}</p>
      <h1 className="mt-1 text-2xl font-semibold text-slate-900">{title}</h1>
      <p className="mt-2 max-w-sm text-sm text-slate-500">{message}</p>
      <Link to="/" className="mt-6 inline-flex min-h-11 items-center rounded-lg bg-navy-800 px-4 text-sm font-medium text-white hover:bg-navy-700">
        Back to dashboard
      </Link>
    </div>
  );
}

export const ForbiddenPage = () => (
  <StatusPage code="403" title="Access denied" message="Your role does not have permission to open this page." />
);

export const NotFoundPage = () => (
  <StatusPage code="404" title="Page not found" message="The page you are looking for does not exist." />
);
