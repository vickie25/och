export function createClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!url || !anonKey) {
    throw new Error('Supabase environment variables are not configured');
  }

  // Supabase is optional in this project. We return a minimal stub to avoid
  // hard dependency on supabase-js in builds where Supabase isn't used.
  const notImplemented = async () => {
    throw new Error('Supabase client is not available in this build');
  };

  return {
    auth: {
      getUser: notImplemented,
    },
    rpc: notImplemented,
    from: () => ({
      upsert: notImplemented,
      update: notImplemented,
      eq: notImplemented,
    }),
    channel: () => ({
      send: notImplemented,
    }),
  } as any;
}
